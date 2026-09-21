Here is a comprehensive set of **30 interview questions and answers** (15 for Django and 15 for Django REST Framework) tailored for a **1–2 years experienced** backend engineer.

---

### **Part 1: Django Core Questions (1–15)**

#### **1. What is the MVT architecture in Django, and how does it differ from MVC?**

* **Answer:** MVT stands for **Model-View-Template**.
* **Model:** The data access layer that handles the database schema and database interactions (ORM).
* **View:** Encapsulates business logic, interacts with models to fetch data, and decides what response to return.
* **Template:** The presentation layer containing HTML and Django Template Language (DTL) syntax.
* **Difference from MVC:** In traditional MVC, the Controller handles incoming requests, interacts with the Model, and passes data to the View. In Django, the **framework itself acts as the controller**, routing the HTTP request to the appropriate View, while the View and Template handle what MVC traditionally splits into Controller and View.



---

#### **2. What is the difference between `select_related()` and `prefetch_related()`?**

* **Answer:** Both are QuerySet optimization methods used to avoid the N+1 query problem, but they work differently based on relationship types:
* **`select_related()`:** Used for **Foreign-Key** and **One-to-One** relationships. It performs a SQL **`JOIN`** and fetches the related object data in the same single query.
* **`prefetch_related()`:** Used for **Many-to-Many** and **Reverse Foreign-Key** relationships. It executes a **separate query** for each relationship and joins them in Python memory using Python-side evaluation.



---

#### **3. Explain Django Middleware and give a practical use case.**

* **Answer:** Middleware is a framework of hooks into Django’s request/response processing pipeline. It’s a light, low-level plugin system that globally alters Django’s input or output.
* **How it works:** Each middleware class is a Python class that receives a `get_response` callable and can run code before (`process_request` equivalent) and after (`process_response` equivalent) the view is called.
* **Use Case:** Implementing custom request logging, tracking execution time for performance monitoring, checking user session tokens or IP throttling.



---

#### **4. What are Django Signals? When should you avoid using them?**

* **Answer:** Signals allow decoupled applications to get notified when certain actions (events) occur elsewhere in the application. Common built-in signals include `post_save`, `pre_save`, and `m2m_changed`.
* **When to avoid:** Signals can make control flow hard to trace and debug because they execute implicitly. Avoid using them for core business logic or complex data mutations; instead, keep them for cross-cutting concerns like auto-creating a profile when a user registers, or clear cache triggers.



---

#### **5. What is the difference between `F()` and `Q()` expressions in Django ORM?**

* **Answer:**
* **`F()` expression:** Represents the value of a model field directly in the database. It allows database operations to happen in the database layer rather than Python memory (e.g., updating stock without race conditions: `Product.objects.filter(id=1).update(stock=F('stock') - 1)`).
* **`Q()` expression:** Used to encapsulate keyword arguments for complex database queries utilizing logical operators like AND (`&`), OR (`|`), and NOT (`~`) (e.g., filtering posts matching title OR author: `Post.objects.filter(Q(title__icontains='django') | Q(author='admin'))`).



---

#### **6. How does Django handle database migrations, and what are the key commands?**

* **Answer:** Migrations are Django’s way of propagating changes you make to your models (adding a field, deleting a model, etc.) into your database schema.
* `python manage.py makemigrations`: Inspects changes in `models.py` and generates new migration files.
* `python manage.py migrate`: Applies pending migration files to the database schema.
* `python manage.py showmigrations`: Displays the status of all migrations (applied or unapplied).



---

#### **7. What are Django managers, and how can you create a custom manager?**

* **Answer:** A Manager is the interface through which database QueryOperations are provided to Django models. By default, Django adds a manager named `objects` to every model.
* **Custom Manager Example:** You create a custom manager to encapsulate reusable query logic (e.g., fetching only published articles):
```python
class PublishedManager(models.Manager):

  def get_queryset(self):
    return super().get_queryset().filter(status='published')


class Article(models.Model):
  title = models.CharField(max_length=100)
  status = models.CharField(max_length=20)
  objects = models.Manager()  # The default manager
  published = PublishedManager()  # Custom manager

```

---

#### **8. What is the difference between `get_object_or_404` and standard `.get()` queries?**
* **Answer:** 
  * A standard `Model.objects.get(pk=1)` raises a `Model.DoesNotExist` exception if the record is missing, which results in a **500 Internal Server Error** unless caught explicitly.
  * `get_object_or_404()` wraps the `.get()` query and raises an **Http404 exception** if the object doesn't exist, cleanly returning a standard Django 404 page or response to the client.

---

#### **9. How does Django handle user authentication and password hashing?**
* **Answer:** Django has a built-in authentication system (`django.contrib.auth`) that handles user accounts, groups, permissions, and cookie-based sessions.
  * **Password Hashing:** Django uses the **PBKDF2** hashing algorithm by default, wrapped with a cryptographic salt (and supports Argon2 as an alternative). Plain-text passwords are never stored in the database.

---

#### **10. Explain Django QuerySet evaluation and laziness.**
* **Answer:** Django QuerySets are **lazy**. Creating a QuerySet (e.g., `users = User.objects.filter(is_active=True)`) does not hit the database. 
  * The database query is only executed when the QuerySet is **evaluated**. Evaluation happens during iteration, slicing, caching, or calling methods like `len()`, `list()`, or `repr()`.

---

#### **11. What is the difference between `abstract = True` and regular model inheritance (multi-table inheritance)?**
* **Answer:**
  * **Abstract Base Classes (`abstract = True` in `Meta`):** Used when you want to put common fields (like `created_at`, `updated_at`) into a base class. Django does **not** create a database table for the abstract class; it only creates tables for the child models containing all combined fields.
  * **Multi-table Inheritance:** Every model in the inheritance hierarchy is a distinct model with its own database table, linked together automatically by an implicit One-to-One field from the child to the parent model.

---

#### **12. How do you implement database transactions in Django?**
* **Answer:** Django provides transaction management via `django.db.transaction`. 
  * The most common approach is using the `atomic` decorator or context manager:
    ```python
    from django.db import transaction


    @transaction.atomic
    def perform_complex_operation():
      # If any exception occurs inside this block, all database queries are rolled back
      Account.objects.filter(id=1).update(balance=F('balance') - 100)
      Ledger.objects.create(amount=100)

    ```

---

#### **13. What is the purpose of Django's CSRF protection, and how does it work?**

* **Answer:** **Cross-Site Request Forgery (CSRF)** protection prevents malicious websites from executing unauthorized actions on behalf of an authenticated user.
* **How it works:** Django sends a random, secret token via a cookie and expects every incoming state-changing request (POST, PUT, DELETE) to submit that token back either via form headers (`X-CSRFToken`) or request bodies. If they don't match, the request is rejected with a 403 error.



---

#### **14. Explain Django custom management commands.**

* **Answer:** Custom management commands allow you to run custom Python scripts via `python manage.py <command_name>`. They are ideal for cron jobs, database seeders, or backend batch processing. They are implemented inside an app's `management/commands/` directory by subclassing `BaseCommand`.

---

#### **15. What are Django forms vs ModelForms?**

* **Answer:**
* **`forms.Form`:** A generic form class used to handle non-model data (e.g., a contact form, login form). You manually define every field and validation logic.
* **`forms.ModelForm`:** Directly tied to a Django Model. It automatically generates form fields matching the model fields, provides built-in model validation, and can easily save or update database records using `.save()`.



---

### **Part 2: Django REST Framework (DRF) Questions (16–30)**

#### **16. What is Django REST Framework (DRF) and why is it used?**

* **Answer:** DRF is a powerful, flexible toolkit built on top of Django designed for building Web APIs[cite: 1]. It simplifies serialization, provides customizable request/response parsers/renderers, supports various authentication and permission schemes out-of-the-box[cite: 1], and features an interactive Web Browsable API[cite: 1].

---

#### **17. What is the difference between `Serializer` and `ModelSerializer` in DRF?**

* **Answer:**
* **`Serializer`:** Similar to a Django `forms.Form`. You must explicitly define every field and write custom `create()` and `update()` methods. It is used for non-model data or custom transformations.
* **`ModelSerializer`:** Similar to a Django `ModelForm`. It automatically generates fields based on the model, provides default implementations for `create()` and `update()`, and intelligently maps model field types to appropriate serializer fields.



---

#### **18. Explain the difference between APIView, GenericAPIView, and ViewSets.**

* **Answer:**
* **`APIView`:** Subclasses Django's `View`, provides basic request dispatching, authentication, and exception handling. You write the CRUD logic manually.
* **`GenericAPIView`:** Extends `APIView` by adding common reusable behaviors for database-backed APIs, such as built-in pagination, filtering, and queryset attributes.
* **`ViewSet`:** Combines logic for a set of related views into a single class without needing explicit method handlers like `.get()` or `.post()`. Instead, it uses actions like `list()`, `create()`, `retrieve()`, `update()`, and works seamlessly with DRF Routers.



---

#### **19. What are DRF Routers, and why use them?**

* **Answer:** Routers automatically generate URL configurations for ViewSets based on standard REST conventions. Instead of writing explicit `path()` routing rules for every single endpoint, using a `DefaultRouter` or `SimpleRouter` registers a ViewSet and instantly sets up all CRUD routing patterns (e.g., `/users/`, `/users/<pk>/`).

---

#### **20. How does authentication differ from authorization (permissions) in DRF?**

* **Answer:**
* **Authentication:** Determines *who* the user is (e.g., verifying a JWT token, session cookie, or Basic Auth header and setting `request.user`).
* **Authorization (Permissions):** Determines *what* an authenticated or unauthenticated user is allowed to do (e.g., checking if `request.user.is_staff` or `IsAuthenticatedOrReadOnly` rules apply before running the view logic).



---

#### **21. How do you handle validation in DRF Serializers?**

* **Answer:** Validation happens during `serializer.is_valid()`. DRF supports three levels of validation:
1. **Field-level validation:** Using `validate_<fieldname>` methods to validate individual fields.
2. **Object-level validation:** Using a `validate(self, data)` method to cross-reference multiple fields.
3. **Validators:** Reusable validator callables assigned directly to serializer fields (e.g., `UniqueValidator`).



---

#### **22. What are Serializer Relations in DRF? Name a few types.**

* **Answer:** Serializer relations define how relationships between models (foreign keys, many-to-many) are serialized. Examples include:
* `StringRelatedField`: Represents the target using its `__str__` output.
* `PrimaryKeyRelatedField`: Represents the target using its primary key ID.
* `HyperlinkedRelatedField`: Represents the target using a hyperlink URL.
* Nested Serializers: Nesting a full serializer inside another (e.g., embedding complete user details inside a post serializer).



---

#### **23. How do you implement Pagination in DRF?**

* **Answer:** DRF supports pagination to break large QuerySets into manageable chunks. Pagination can be set globally in `settings.py` under `REST_FRAMEWORK` or overridden locally per view. Common styles include:
* **PageNumberPagination:** Returns pages with page sizes and count headers (e.g., `?page=2`).
* **LimitOffsetPagination:** Uses `limit` and `offset` query parameters (e.g., `?limit=10&offset=20`).
* **CursorPagination:** Uses a cursor-based approach for high-performance pagination on large datasets.



---

#### **24. What is Throttling in DRF, and how does it work?**

* **Answer:** Throttling restricts the rate of requests that a client can make to an API, protecting against scraping, brute-force attacks, or denial of service. DRF provides built-in throttle classes like `AnonRateThrottle` and `UserRateThrottle`, which track request counts over a specific time window using cache systems.

---

#### **25. How do you implement Filtering and Searching in a DRF API?**

* **Answer:** You can use third-party packages like `django-filter` or DRF's built-in filter backends.
* **Filtering:** Using `DjangoFilterBackend` to allow precise filtering on model fields.
* **Searching:** Using `SearchFilter` to execute partial text searches across text fields using a `?search=query` parameter.
* **Ordering:** Using `OrderingFilter` to sort results dynamically via `?ordering=field_name`.



---

#### **26. What is Content Negotiation in DRF?**

* **Answer:** Content negotiation is the mechanism DRF uses to determine which renderer (e.g., `JSONRenderer`, `BrowsableAPIRenderer`) should be used to format the outgoing response based on client requests (such as the `Accept` header) or parser handling for incoming payloads.

---

#### **27. How do you handle custom exceptions in DRF?**

* **Answer:** DRF provides a default exception handler function (`rest_framework.views.exception_handler`) that converts standard Python/Django exceptions into appropriate HTTP status responses (like 404, 400, 401). You can customize this by writing a custom wrapper function to intercept specific errors and format the JSON error payload uniformly across your API.

---

#### **28. What is the purpose of `partial=True` in DRF serializers?**

* **Answer:** By default, calling `serializer.save()` on a serializer instance expects all required fields to be present (fulfilling a PUT request). Setting `partial=True` (typically used in PATCH requests) tells the serializer that updates can be partial, meaning missing fields are ignored and validation won't fail if only subset fields are updated.

---

#### **29. How do you write unit tests for a DRF API?**

* **Answer:** DRF provides a specialized `APITestCase` class subclassing Django's standard test case. It includes an `APIClient` capable of handling credential headers, token authentication, and testing standard HTTP verbs (`client.get()`, `client.post()`, `client.put()`) while asserting response status codes and JSON payloads.

---

#### **30. How can you optimize performance for a heavily loaded DRF API endpoint?**

* **Answer:** Key optimization steps include:
1. Using `.select_related()` and `.prefetch_related()` in your ViewSet's `queryset` to prevent N+1 queries.
2. Implementing proper caching mechanisms (e.g., Django cache framework or view caching).
3. Using lightweight serializers or field restriction (`fields` option) to avoid serializing heavy or unnecessary columns.
4. Adding database indexing on frequently filtered or sorted fields.