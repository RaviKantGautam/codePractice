Here is a comprehensive set of **30 interview questions and answers** (15 for Django and 15 for Django REST Framework) customized for a **3–4 years experienced** backend engineer. These questions delve deeper into architectural trade-offs, advanced ORM optimizations, security, asynchronous capabilities, scaling patterns, and recent features (such as **Django 6.1 fetch modes and database-level cascades**).

---

### **Part 1: Advanced Django Core Questions (1–15)**

#### **1. How does Django handle the N+1 query problem, and what are the newer options available for handling query fetching?**

* **Answer:**
* Traditionally, Django resolves N+1 query problems using `.select_related()` (for Foreign-Key/One-to-One SQL joins) and `.prefetch_related()` (for Many-to-Many/Reverse Foreign-Key Python-side joins).
* **Django 6.1 Addition:** Django 6.1 introduced model field **fetch modes** via `QuerySet.fetch_mode()`:
* `FETCH_ONE`: Default behavior fetching missing fields for the single current instance.
* `FETCH_PEERS`: Acts like an automatic on-demand `prefetch_related()`, fetching missing foreign-key fields for all instances loaded by the same queryset in just two queries.
* `FETCH_RAISE`: Raises a `FieldFetchBlocked` exception, safeguarding performance-critical blocks against accidental lazy queries.





---

#### **2. Compare Python-level `on_delete` behaviors with database-level delete options introduced recently.**

* **Answer:**
* *Python-level:* Django traditionally enforced options like `models.CASCADE`, `models.SET_NULL`, or `models.SET_DEFAULT` inside Python, meaning Django had to fetch related model instances into memory before issuing delete commands. This also triggered `pre_delete` and `post_delete` signals.
* *Database-level (Django 6.1+):* ForeignKey `on_delete` now supports database-level delete choices (`DB_CASCADE`, `DB_SET_NULL`, `DB_SET_DEFAULT`) which delegate deletion logic directly to the database via SQL `ON DELETE` clauses, providing significantly higher deletion performance without loading objects into memory (though they bypass Django delete signals).



---

#### **3. How do you implement and scale custom database routing in a multi-tenant or multi-database Django architecture?**

* **Answer:** You configure a database router class implementing up to four methods: `db_for_read(model, **hints)`, `db_for_write(model, **hints)`, `allow_relation(obj1, obj2, **hints)`, and `allow_migrate(db, app_label, model_name=None, **hints)`.
* To scale this for multi-tenancy (e.g., database-per-tenant), you typically bind tenant context dynamically to thread-local storage or context variables (`contextvars`), and have your database router inspect that context to dynamically return the appropriate database alias.



---

#### **4. Explain the execution pipeline of Django Middleware and how asynchronous middleware differs.**

* **Answer:**
* *Synchronous Pipeline:* Incoming requests pass through each middleware's `process_request` (or factory function), hit the view, and the response passes backward through `process_response`.
* *Asynchronous / Hybrid Pipeline:* Starting with async support, Django inspects middleware flags (`sync_capable` and `async_capable`). If a middleware isn't marked as async-safe, Django synchronously wraps it, which can incur performance costs (thread-pool context switches). Pure ASGI/async middleware must correctly handle coroutines (`await get_response(request)`).



---

#### **5. What are Django Database Transactions, and how do atomic blocks behave with nested calls and savepoints?**

* **Answer:** `transaction.atomic()` manages transaction blocks. When nested, outer blocks wrap inner blocks using **database savepoints** (`SAVEPOINT`). If an exception is raised in an inner atomic block, only the database changes made inside that inner block are rolled back to the savepoint, whereas outer transactions remain intact unless the inner exception bubbles up unhandled.

---

#### **6. How do you design and execute atomic updates using `F()` expressions to avoid race conditions?**

* **Answer:** Race conditions happen when two requests read a value, modify it in Python memory, and write it back concurrently (lost updates).
* Using `F()` expressions forces the database to perform calculations natively in SQL.
* *Example:* `Product.objects.filter(pk=1).update(stock=F('stock') - 1)` ensures the update statement translates to `UPDATE product SET stock = stock - 1 WHERE id = 1`, avoiding concurrent overwrite bugs.



---

#### **7. Explain Django’s ContentTypes framework and name a practical architectural use case.**

* **Answer:** `django.contrib.contenttypes` tracks all installed models in your project, creating a record in a `ContentType` table for each.
* *Use Case:* Implementing **Generic Relations** (`GenericForeignKey` and `GenericRelation`). This allows a single model (like a global Comments or Activity Audit Log system) to link dynamically to any other model in your application without needing explicit foreign keys for every table.



---

#### **8. How do custom QuerySets and Managers differ, and when should you chain methods on QuerySets vs Managers?**

* **Answer:**
* **Manager:** The entry point for QuerySets on a model (e.g., `Model.objects`). Custom managers should contain global filters or table-level table operations you want available everywhere (e.g., `Book.objects.active()`).
* **QuerySet:** Represents a lazy collection of database rows. Custom QuerySet methods allow chaining (e.g., `Book.objects.active().recent()`), because custom QuerySet methods return a new QuerySet instance, unlike standard Manager methods which don't always chain seamlessly unless mirrored.



---

#### **9. How would you handle database connection pooling in high-traffic production Django apps?**

* **Answer:** Django's default behavior opens a new database connection per request and closes it at the end. For high-traffic setups, this causes performance bottlenecks. Solutions include:
* Using external connection poolers like **PgBouncer** (for PostgreSQL) in transaction or session mode.
* Utilizing database connection persistent options (setting `CONN_MAX_AGE` in `DATABASES` settings to keep connections alive for a specified number of seconds or permanently via `None`).



---

#### **10. What are deferred fields (`defer()` and `only()`), and what are their performance trade-offs?**

* **Answer:**
* `defer('field_name')`: Loads all model fields *except* the specified ones, fetching them lazily on-demand when accessed.
* `only('field_name')`: Loads *only* the specified fields, deferring all others.
* *Trade-off:* While they save memory and network payload when dealing with large text/binary columns, looping through deferred fields can trigger an N+1 query storm if you inadvertently access deferred attributes across thousands of list items.



---

#### **11. How does Django handle database indexing, and how do you create partial or functional indexes?**

* **Answer:** Beyond standard `db_index=True` or `unique=True`, Django supports advanced index configuration inside model `Meta.indexes`:
* *Functional Indexes:* Indexing expressions or functions (e.g., indexing lower-case versions of email fields: `Index(Lower('email'), name='lower_email_idx')`).
* *Partial Indexes:* Indexing rows matching a specific condition using `condition=Q(...)` (e.g., indexing only active user records).



---

#### **12. Explain how Django Custom Management Commands are structured and how you handle long-running batch operations safely.**

* **Answer:** Custom management commands reside inside `management/commands/<command_name>.py`, subclassing `BaseCommand`.
* For long-running production tasks, you should handle transaction atomicity carefully (avoid wrapping multi-hour loops in a single massive `atomic` block to prevent memory bloat and table locks), add robust logging, incorporate batch chunking (e.g., `iterator(chunk_size=1000)`), and handle cancellation signals gracefully.



---

#### **13. What is the difference between Django Signals and custom method overrides or service layers?**

* **Answer:**
* *Signals:* Implicit, decoupled, and execute globally. They are hard to trace and can introduce hidden side effects during testing or bulk operations (`bulk_create` doesn't trigger `post_save`).
* *Service Layers / Explicit Methods:* Explicitly calling functions or overriding model `.save()` methods offers clean traceability, explicit dependency injection, and easier unit testing, making it preferred for core domain business logic.



---

#### **14. How do you implement custom database lookups in Django ORM?**

* **Answer:** You can extend Django’s lookup registry to create custom SQL conditional clauses (e.g., matching a custom regex or custom SQL operator). This involves subclassing `models.Lookup`, registering it with a field type using `models.Field.register_lookup()`, and defining the SQL compilation logic (`as_sql`).

---

#### **15. How do you manage asynchronous tasks or background workers in modern Django apps?**

* **Answer:** Historically handled by third-party task brokers like **Celery** or **Django-Q**. Django also features native integration hooks and background runner specifications, but production systems typically utilize Redis/RabbitMQ brokers with Celery or Dramatiq to process emails, report generation, and heavy data-processing pipelines asynchronously outside the request-response cycle.

---

### **Part 2: Advanced Django REST Framework (DRF) Questions (16–30)**

#### **16. Explain the inner lifecycle of a DRF Request from dispatch to response.**

* **Answer:** When an API request hits a DRF view:
1. Django routes the request to DRF’s `APIView.as_view()`.
2. DRF initializes a wrapper `Request` object instead of a standard Django request.
3. **Authentication** classes run to identify `request.user`.
4. **Permissions** classes run to check authorization rules.
5. **Throttling** checks request rate limits.
6. The appropriate HTTP method handler (`get`, `post`, etc.) executes.
7. **Serialization/Deserialization** validates and transforms data.
8. **Content Negotiation** determines the correct renderer (JSON, Browsable API), and DRF returns a formatted `Response`.



---

#### **17. How do you optimize serialization performance for high-throughput DRF endpoints containing complex relations?**

* **Answer:**
* Avoid deep, nested serializers with heavy database queries inside loops.
* Ensure the underlying ViewSet QuerySet uses `.select_related()` and `.prefetch_related()` aggressively.
* Utilize specialized lightweight relations (`PrimaryKeyRelatedField` or `SlugRelatedField`) instead of full nested representations where appropriate.
* Consider third-party high-performance serializers (like `django-rest-framework-json-api` or caching serialized dictionary outputs using Redis).



---

#### **18. How do you implement object-level permissions in DRF?**

* **Answer:** While global permissions check if a user can access an endpoint generally, **object-level permissions** determine if a user can access a specific instance (e.g., editing only their own blog post).
* This is implemented by creating a custom permission subclassing `BasePermission` and overriding `has_object_permission(self, request, view, obj)`, then ensuring your view calls `.check_object_permissions(request, obj)` or uses Generic views that invoke it automatically.



---

#### **19. What are DRF ViewSets and Routers, and how do you write custom actions in a ViewSet?**

* **Answer:**
* **ViewSets** consolidate multiple view logics (list, create, retrieve, update, destroy) into a single class.
* **Routers** map ViewSets to URL paths automatically.
* **Custom Actions:** Created using the `@action` decorator, allowing you to expose custom endpoints on a ViewSet.
```python
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets


class UserViewSet(viewsets.ModelViewSet):
  queryset = User.objects.all()

  @action(detail=True, methods=['post'])
  def set_password(self, request, pk=None):
    user = self.get_object()
    # custom business logic here
    return Response({'status': 'password set'})

```

---

#### **20. How do you handle complex transaction boundaries and validation inside DRF Serializer `create()` or `update()` methods?**
* **Answer:** For multi-model creation (e.g., creating an Order and multiple OrderItems simultaneously), you should wrap the saving logic inside a `transaction.atomic()` block inside the serializer's `create()` method. If any child item creation fails, the entire transaction rolls back, preventing orphaned records.

---

#### **21. Explain how DRF handles content negotiation and how you can add a custom renderer or parser.**
* **Answer:** 
  * Content negotiation evaluates client `Accept` headers against available renderers configured in `DEFAULT_RENDERER_CLASSES`.
  * *Custom Renderer/Parser:* Subclass `rest_framework.renderers.BaseRenderer` (defining media type and a `render()` method) or `rest_framework.parsers.BaseParser` (defining a `parse()` method), and register them globally or per-view.

---

#### **22. How do you implement token-based authentication (such as JWT) in DRF?**
* **Answer:** DRF supports token authentication out of the box, but JSON Web Tokens (JWT) are industry standard for stateless scaling. This is typically implemented using third-party packages like `djangorestframework-simplejwt`. 
  * The client sends credentials to a token endpoint, receives an access token and refresh token, and passes the access token in the `Authorization: Bearer <token>` header for subsequent requests.

---

#### **23. How do you implement robust filtering, searching, and ordering in DRF APIs?**
* **Answer:** 
  * Configure `DEFAULT_FILTER_BACKENDS` in settings using DRF’s built-in `DjangoFilterBackend`, `SearchFilter`, and `OrderingFilter`.
  * Specify `filterset_class` or `filter_backends`, `search_fields = ['title', 'content']`, and `ordering_fields = ['created_at']` on your ViewSet to let clients query parameters like `?search=django&ordering=-created_at`.

---

#### **24. How do you customize default error handling and format uniform error responses across a DRF application?**
* **Answer:** DRF’s default exception handler (`rest_framework.views.exception_handler`) converts standard exceptions into structured error dicts. To customize it, write a wrapper function that checks if the exception was caught by DRF, extracts the error details, and restructures the JSON body into a standard format (e.g., `{"success": false, "error": {"code": 400, "message": "...", "details": ...}}`), then points to it in `REST_FRAMEWORK['EXCEPTION_HANDLER']`.

---

#### **25. What is API throttling, and how would you configure custom rate limits for specific high-cost endpoints?**
* **Answer:** Throttling controls request frequency. DRF provides classes like `UserRateThrottle` and `AnonRateThrottle`. 
  * To customize throttling for specific endpoints, you can subclass `SimpleRateThrottle`, override `get_cache_key()` to target specific user tiers or actions, and assign the custom throttle class to a specific ViewSet via `throttle_classes = [CustomTierThrottle]`.

---

#### **26. How do you write integration and unit tests for DRF endpoints using `APITestCase`?**
* **Answer:** Subclass `rest_framework.test.APITestCase`, which provides an instance of `APIClient`. 
  * You can test endpoints by authenticating the client (`client.force_authenticate(user=self.user)` or passing bearer tokens), executing HTTP verbs (`client.get()`, `client.post(url, data, format='json')`), and asserting response status codes (`status.HTTP_200_OK`) and JSON payload structures.

---

#### **27. How do you manage API versioning in DRF?**
* **Answer:** DRF supports several versioning schemes configured via `DEFAULT_VERSIONING_CLASS`:
  * **URL Path Versioning:** `/api/v1/users/` (using `URLPathVersioning`).
  * **Namespace Versioning:** Using Django URL namespaces.
  * **Accept Header Versioning:** Passing version info in the HTTP `Accept` header (e.g., `application/json; version=1.0`).
  * **Query Parameter Versioning:** `/api/users/?version=1.0`.

---

#### **28. How do you handle file uploads and image processing efficiently in DRF APIs?**
* **Answer:** 
  * Use `FileField` or `ImageField` in serializers, which accept `multipart/form-data`.
  * For performance, avoid processing heavy image resizing or virus scanning synchronously inside the request-response cycle; instead, save the raw uploaded file to cloud storage (via `django-storages` with AWS S3/GCP) and trigger an asynchronous Celery worker task to handle resizing and optimization.

---

#### **29. What is the purpose of the Browsable API in DRF, and how do you secure or disable it in production?**
* **Answer:** 
  * The Browsable API renders an interactive HTML GUI for all API endpoints, making debugging and testing developer-friendly.
  * *Security/Production:* In production environments, it should either be restricted to admin-only permissions or completely disabled by removing `rest_framework.renderers.BrowsableAPIRenderer` from your global `DEFAULT_RENDERER_CLASSES` settings to prevent potential data exposure or CSRF vectors.

---

#### **30. How do you implement cursor-based pagination in DRF, and why choose it over page-number pagination for large tables?**
* **Answer:** 
  * **PageNumberPagination** uses SQL `OFFSET` and `LIMIT` queries (`OFFSET 100000 LIMIT 10`). As tables grow into millions of rows, `OFFSET` scanning becomes drastically slow because the database still reads through preceding rows.
  * **CursorPagination** uses encoded pointers (cursors) based on unique, ordered fields (like timestamp or ID) and queries using direct lookups (`WHERE id > last_seen_id LIMIT 10`), guaranteeing constant $O(1)$ query performance regardless of how deep the user is in pagination results.
