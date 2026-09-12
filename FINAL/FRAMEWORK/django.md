# Django Interview Questions & Answers

> Interview prep notes covering Django core, ORM, DRF, Celery, caching, security, and coding problems.

---

## Table of Contents

1. [Architecture & Basics](#1-architecture--basics)
2. [Views, Mixins & Middleware](#2-views-mixins--middleware)
3. [Models, Managers & ORM](#3-models-managers--orm)
4. [Database, Transactions & Performance](#4-database-transactions--performance)
5. [Auth, Sessions, Caching & Security](#5-auth-sessions-caching--security)
6. [Celery, Logging & Management Commands](#6-celery-logging--management-commands)
7. [DRF / REST API](#7-drf--rest-api)
8. [API Observability](#8-api-observability)
9. [Django Coding Questions](#9-django-coding-questions)

---

## 1. Architecture & Basics

### What is MVT architecture?

**MVT** = **Model – View – Template** (Django’s architectural pattern).

| Layer | Role |
|-------|------|
| **Model** | Data layer — maps to DB tables via Django ORM (`models.py`) |
| **View** | Business / request logic — receives HTTP request, talks to Model, returns response |
| **Template** | Presentation layer — HTML (or other) rendered with context data |

**Flow:**
1. URL router matches request → View
2. View queries Model(s)
3. View passes data to Template (or returns JSON in APIs)
4. Response sent back to client

**MVT vs MVC:** Same idea as MVC, but Django’s **View** ≈ MVC Controller, and Django’s **Template** ≈ MVC View. Django’s “View” is the request handler, not the UI.

---

### Explain the architectural pattern of Django

Django follows **MVT** plus supporting layers:

```
Client Request
    → WSGI/ASGI Server (Gunicorn / Uvicorn / uWSGI)
        → Django Middleware stack
            → URL Dispatcher (urls.py)
                → View (FBV / CBV / DRF ViewSet)
                    → Model / Manager / QuerySet (ORM)
                    → Template / Serializer (response)
                ← HttpResponse / JSON
        ← Middleware (response phase)
    ← Client
```

**Key Django design ideas:**
- **Batteries included** — ORM, admin, auth, sessions, forms, i18n
- **Loose coupling** — apps are reusable packages
- **DRY** — shared base models, mixins, generic views
- **Explicit over implicit** — settings, URLconf, `INSTALLED_APPS`

---

### What is WSGI and uWSGI?

**WSGI (Web Server Gateway Interface)**  
- Python standard (PEP 3333) defining how a web server talks to a Python web app.
- Synchronous interface.
- Django’s traditional entry: `wsgi.py` → `get_wsgi_application()`.
- Servers that speak WSGI: **Gunicorn**, **uWSGI**, **mod_wsgi**.

**ASGI** (not asked, but related) — async successor; used with Django Channels / async views (`asgi.py`).

**uWSGI**  
- A **production application server** that can host WSGI apps (Django, Flask, etc.).
- Features: process management, buffering, routing, Emperor mode, cheaper modes.
- Often sits behind Nginx:
  `Client → Nginx → uWSGI → Django`

| Term | What it is |
|------|------------|
| WSGI | Spec / protocol |
| uWSGI | Server implementation that speaks WSGI (and more) |
| Gunicorn | Another popular WSGI server |

---

### What is payload?

**Payload** = the actual data carried in an HTTP request/response body (excluding headers/metadata).

Examples:
- JSON body in `POST /api/users/` → `{"name": "Ravi", "email": "ravi@x.com"}`
- Form data in a file upload
- Response body returned by the API

In APIs, “validate the payload” means validate request body fields (often via DRF serializers).

---

## 2. Views, Mixins & Middleware

### What are Mixins?

**Mixins** are reusable classes that provide a focused piece of behavior to be combined into other classes via multiple inheritance.

In Django CBVs / DRF:
- `LoginRequiredMixin` — require auth
- `PermissionRequiredMixin` — require permissions
- `SingleObjectMixin`, `MultipleObjectMixin`
- DRF: custom mixins like `CreateModelMixin`, `ListModelMixin`

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

class MyListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "articles.html"
```

**Rules:** Mixins should be small, orthogonal, and listed **before** the base view in the MRO.

---

### Difference between Class-Based Views (CBV) and Function-Based Views (FBV)

| Aspect | FBV | CBV |
|--------|-----|-----|
| Style | One function handles a request | Class methods (`get`, `post`, …) |
| Reuse | Harder (copy/decorators) | Easy via inheritance + mixins |
| Generics | Manual | Built-in (`ListView`, `CreateView`, …) |
| Readability | Clear for simple logic | Better for CRUD / shared structure |
| Learning curve | Lower | Higher (MRO, `as_view()`) |

```python
# FBV
def article_list(request):
    articles = Article.objects.all()
    return render(request, "list.html", {"articles": articles})

# CBV
class ArticleListView(ListView):
    model = Article
    template_name = "list.html"
```

**Interview tip:** Prefer FBV for simple one-off logic; prefer CBV/DRF generics/viewsets for CRUD and reuse.

---

### What are middlewares?

**Middleware** = a hook into Django’s request/response pipeline. Each middleware can process the request on the way in and the response on the way out.

Order in `MIDDLEWARE` matters (top → bottom on request; reverse on response).

**Common uses:**
- Auth / session
- CSRF protection
- Security headers
- Logging, timing, compression
- IP blocking, rate limiting, API version routing

Built-in examples: `SecurityMiddleware`, `SessionMiddleware`, `AuthenticationMiddleware`, `CsrfViewMiddleware`, `XFrameOptionsMiddleware`.

---

### Logging HTTP Requests and Responses (Django + DRF)

Custom middleware example:

```python
# myapp/middleware.py
import logging
import time

logger = logging.getLogger("http")

class RequestResponseLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        body = request.body[:1000] if request.body else b""
        logger.info("REQ %s %s body=%s", request.method, request.path, body)

        response = self.get_response(request)

        duration_ms = (time.time() - start) * 1000
        logger.info(
            "RES %s %s status=%s took=%.2fms",
            request.method, request.path, response.status_code, duration_ms,
        )
        return response
```

```python
# settings.py
MIDDLEWARE = [
    # ...
    "myapp.middleware.RequestResponseLoggingMiddleware",
]

LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"http": {"handlers": ["console"], "level": "INFO"}},
}
```

**Caution:** Never log passwords, tokens, or full sensitive payloads in production.

---

## 3. Models, Managers & ORM

### What are the model inheritance styles in Django?

Django supports **3** inheritance styles:

#### 1) Abstract Base Classes
- `class Meta: abstract = True`
- Parent has **no** DB table
- Fields copied into child tables
- Best for shared fields (`created_at`, `updated_at`)

```python
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Product(BaseModel):
    name = models.CharField(max_length=100)
```

#### 2) Multi-table Inheritance
- Parent **has** a table; child has its own table + OneToOne link to parent
- Allows querying parent for all subtypes
- Extra JOINs — use carefully

```python
class Place(models.Model):
    name = models.CharField(max_length=50)

class Restaurant(Place):
    serves_pizza = models.BooleanField(default=False)
```

#### 3) Proxy Models
- Same DB table as parent
- Change Python behavior only (managers, ordering, methods)
- `class Meta: proxy = True`

```python
class Person(models.Model):
    name = models.CharField(max_length=100)

class MyPerson(Person):
    class Meta:
        proxy = True
        ordering = ["name"]
```

---

### What is use of BaseModel in Django?

A **BaseModel** (abstract) is a shared parent that holds common fields/methods for all models:

Typical fields:
- `id` / UUID primary key
- `created_at`, `updated_at`
- `is_active` / soft delete (`deleted_at`)
- `created_by`

**Why:** DRY, consistent auditing, one place to add cross-cutting model behavior.

---

### Can we write a custom QuerySet in Django? How?

Yes. Subclass `models.QuerySet`, add chainable methods, then attach via Manager.

```python
class BookQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def by_author(self, author_id):
        return self.filter(author_id=author_id)

class BookManager(models.Manager):
    def get_queryset(self):
        return BookQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

class Book(models.Model):
    title = models.CharField(max_length=200)
    is_published = models.BooleanField(default=False)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)

    objects = BookManager()

# Usage
Book.objects.published().by_author(5)
```

Shortcut:

```python
class Book(models.Model):
    ...
    objects = BookQuerySet.as_manager()
```

---

### What is Model Manager?

A **Manager** is the interface through which Django models query the database. Default is `Model.objects`.

Responsibilities:
- Starting point for QuerySets (`objects.all()`, `filter()`, …)
- Encapsulate business query logic
- Can restrict default queryset (e.g. soft-delete aware manager)

```python
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Article(models.Model):
    is_active = models.BooleanField(default=True)
    objects = models.Manager()       # all rows
    active = ActiveManager()         # only active
```

---

### Q lookup / operator

**`Q` objects** build complex queries with OR / AND / NOT.

```python
from django.db.models import Q

# OR
User.objects.filter(Q(email__icontains="gmail") | Q(username__icontains="admin"))

# AND + NOT
Product.objects.filter(Q(price__gte=100) & ~Q(is_deleted=True))

# Dynamic
query = Q()
if search:
    query &= Q(title__icontains=search) | Q(body__icontains=search)
Article.objects.filter(query)
```

Field lookups: `__exact`, `__iexact`, `__contains`, `__icontains`, `__in`, `__gt`, `__gte`, `__lt`, `__lte`, `__startswith`, `__isnull`, `__year`, etc.

---

### Difference between `filter()` and `get()` in Django ORM

| | `filter()` | `get()` |
|--|------------|---------|
| Returns | QuerySet (0..N) | Single model instance |
| No match | Empty QuerySet | `DoesNotExist` |
| Multiple matches | All matches | `MultipleObjectsReturned` |
| Lazy? | Yes | Evaluates immediately |

```python
users = User.objects.filter(is_active=True)   # queryset
user = User.objects.get(pk=1)                 # one object or exception
```

Use `get()` when you expect exactly one row (by PK/unique field). Prefer `filter().first()` when zero results are OK.

---

### How do you update a record using Django ORM?

```python
# 1) Fetch + save
u = User.objects.get(pk=1)
u.email = "new@example.com"
u.save(update_fields=["email"])

# 2) QuerySet.update (no signals, no save(), bulk SQL UPDATE)
User.objects.filter(pk=1).update(email="new@example.com")

# 3) update_or_create
obj, created = User.objects.update_or_create(
    email="a@x.com",
    defaults={"name": "Ravi"},
)

# 4) F expressions (atomic relative update)
from django.db.models import F
Product.objects.filter(pk=1).update(stock=F("stock") - 1)
```

---

### F expression

**`F()`** references a model field value in the DB, so updates/comparisons happen in SQL without race-prone read-modify-write in Python.

```python
from django.db.models import F

# Increment without race
Account.objects.filter(pk=1).update(balance=F("balance") + 100)

# Compare two fields
Order.objects.filter(amount__gt=F("paid_amount"))

# With annotation
from django.db.models import F, ExpressionWrapper, DecimalField
Product.objects.annotate(
    discounted=ExpressionWrapper(F("price") * 0.9, output_field=DecimalField())
)
```

Pair with `transaction.atomic()` for critical money/inventory flows.

---

### Annotation vs Aggregation in Django

| | Annotation | Aggregation |
|--|------------|-------------|
| Scope | Per-row computed field on QuerySet | Collapse QuerySet into summary value(s) |
| Returns | QuerySet (still iterable models) | Dict (usually) |
| Example | count of related books per author | total books in DB |

```python
from django.db.models import Count, Avg, Sum

# Annotation — each author gets book_count
authors = Author.objects.annotate(book_count=Count("book"))

# Aggregation — single summary
stats = Book.objects.aggregate(
    total=Count("id"),
    avg_price=Avg("price"),
    revenue=Sum("price"),
)
# {'total': 10, 'avg_price': 250.0, 'revenue': 2500}
```

---

### QuerySet Evaluation

QuerySets are **lazy** — no DB hit until evaluated.

**Evaluated when:**
- Iteration (`for obj in qs`)
- `list(qs)`, `bool(qs)`, `len(qs)`
- Slicing with evaluation, `qs[0]`
- `repr(qs)` in shell
- Calling `list`-forcing methods sometimes indirectly

**Caching:** After first evaluation, results are cached on that QuerySet instance. Reusing the same QS avoids a second query; calling `.all()` / new filter creates a new QS.

```python
qs = Book.objects.filter(is_published=True)  # no query yet
print(qs.count())  # hits DB (COUNT)
for b in qs:       # hits DB again (SELECT) — count didn't populate cache of objects
    ...
for b in qs:       # uses cache — no new query
    ...
```

---

### How to use JOIN in ORM

Django creates JOINs via:
1. **Lookups across relations** → `filter(author__name="Ravi")`
2. **`select_related`** → SQL JOIN for FK/OneToOne (forward)
3. **`prefetch_related`** → separate query (+ join table for M2M), not always a SQL JOIN

```python
# Implicit JOIN in WHERE
Book.objects.filter(author__country="IN")

# Explicit eager JOIN (FK)
Book.objects.select_related("author", "publisher")

# Reverse / M2M
Author.objects.prefetch_related("book_set", "tags")
```

---

### ORM: Second highest salary of employee in Python Department

```python
from django.db.models import Max

# Option A — exclude the max, then take new max
second = (
    Employee.objects
    .filter(department__name="Python")
    .exclude(
        salary=Employee.objects.filter(department__name="Python").aggregate(m=Max("salary"))["m"]
    )
    .aggregate(second=Max("salary"))["second"]
)

# Option B — order + distinct salaries
salaries = (
    Employee.objects
    .filter(department__name="Python")
    .order_by("-salary")
    .values_list("salary", flat=True)
    .distinct()
)
second_highest = list(salaries[:2])[1] if salaries.count() >= 2 else None

# Option C — employee row(s) with 2nd highest salary
top_two = (
    Employee.objects
    .filter(department__name="Python")
    .order_by("-salary")
    .values_list("salary", flat=True)
    .distinct()[:2]
)
if len(list(top_two)) == 2:
    second_salary = list(top_two)[1]
    employees = Employee.objects.filter(
        department__name="Python", salary=second_salary
    )


from django.db.models import F, Window
from django.db.models.functions import DenseRank
from myapp.models import Employee

# Rank employees within each department
ranked_by_dept = Employee.objects.annotate(
    dept_rank=Window(
        expression=DenseRank(),
        partition_by=[F('department_id')],
        order_by=F('salary').desc()
    )
)
```

---

### How would you find the top 5 authors with the most books?

```python
from django.db.models import Count

top_authors = (
    Author.objects
    .annotate(book_count=Count("book"))
    .order_by("-book_count")[:5]
)
```

---

## 4. Database, Transactions & Performance

### Multiple Database setup

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "primary_db",
        "USER": "user",
        "PASSWORD": "pass",
        "HOST": "db1",
        "PORT": "5432",
    },
    "replica": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "replica_db",
        "USER": "user",
        "PASSWORD": "pass",
        "HOST": "db2",
        "PORT": "5432",
    },
}

DATABASE_ROUTERS = ["myproject.db_router.PrimaryReplicaRouter"]
```

```python
# db_router.py
class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        return "replica"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
```

Manual:

```python
User.objects.using("replica").all()
user.save(using="default")
```

---

### Django connection pooling with PostgreSQL

**Options:**

1. **`CONN_MAX_AGE`** — persistent connections per worker (not a full pool)
2. **Native pool (Django 5.1+)** with `psycopg[pool]`
3. **External pooler** — PgBouncer (common in production)

```python
# Django 5.1+ native pooling (requires psycopg3 + psycopg-pool)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mydb",
        "USER": "user",
        "PASSWORD": "pass",
        "HOST": "localhost",
        "PORT": "5432",
        "CONN_MAX_AGE": 0,  # required with pool
        "OPTIONS": {
            "pool": {
                "min_size": 4,
                "max_size": 16,
                "timeout": 10,
                "max_lifetime": 1800,
                "max_idle": 300,
            },
        },
    }
}
```

Or `"pool": True` for defaults. Incompatible with non-zero `CONN_MAX_AGE`. For ASGI / many workers, **PgBouncer** is still a strong production choice.

---

### Atomic Transactions in Django

```python
from django.db import transaction

@transaction.atomic
def transfer(from_id, to_id, amount):
    a = Account.objects.select_for_update().get(pk=from_id)
    b = Account.objects.select_for_update().get(pk=to_id)
    a.balance -= amount
    b.balance += amount
    a.save()
    b.save()

# Context manager
with transaction.atomic():
    Order.objects.create(...)
    Inventory.objects.filter(...).update(stock=F("stock") - 1)

# Savepoint / nested
with transaction.atomic():
    do_something()
    try:
        with transaction.atomic():  # savepoint
            risky()
    except Exception:
        handle()
```

`ATOMIC_REQUESTS = True` wraps each request in a transaction (usually avoid globally — prefer explicit `atomic()`).

---

### Difference between `select_related` and `prefetch_related`

| | `select_related` | `prefetch_related` |
|--|------------------|--------------------|
| Mechanism | SQL **JOIN** (single query) | Extra query(ies), join in Python |
| Relations | FK, OneToOne (forward) | Reverse FK, M2M, also FK |
| Best for | Many-to-one / one-to-one | One-to-many / many-to-many |

```python
# 1 query with JOINs
Book.objects.select_related("author", "publisher")

# 2 queries (authors + books)
Author.objects.prefetch_related("book_set")

# Fine-grained
from django.db.models import Prefetch
Author.objects.prefetch_related(
    Prefetch("book_set", queryset=Book.objects.filter(is_published=True))
)
```

---

### Explain Django Migrations — `makemigrations` vs `migrate`

| Command | What it does |
|---------|----------------|
| `makemigrations` | Detects model changes → writes migration files under `migrations/` |
| `migrate` | Applies pending migrations to the database |
| `showmigrations` | Shows applied / unapplied |
| `sqlmigrate app 0002` | Prints SQL for a migration |

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py migrate myapp 0003   # migrate to specific
```

Migration files are version control for schema — commit them.

---

### How can we revert an applied migration?

```bash
# Roll back myapp to migration 0002 (unapplies 0003+)
python manage.py migrate myapp 0002

# Unapply all migrations of an app
python manage.py migrate myapp zero
```

Or add a **reverse** migration / RunPython with `reverse_code`.  
**Never** delete applied migration files casually on shared/prod DBs — reverse properly, then create new migrations.

---

### Optimizing Django QuerySet Performance

1. Use `select_related` / `prefetch_related` (fix N+1)
2. `only()` / `defer()` — fetch needed columns
3. `values()` / `values_list()` — dicts/tuples when model instances aren’t needed
4. `count()`, `exists()` instead of `len(list(qs))`
5. `iterator()` for huge result sets (stream, less memory)
6. `bulk_create`, `bulk_update`
7. DB indexes on filtered/joined fields
8. Avoid `qs[0]` in loops; paginate
9. Cache hot QuerySets (Redis)
10. `explain()` / Django Debug Toolbar / `connection.queries`

---

### N + 1 Query Problem

**Problem:** 1 query for parents + N queries for related objects in a loop.

```python
# BAD — N+1
books = Book.objects.all()
for book in books:
    print(book.author.name)  # extra query each time

# GOOD
books = Book.objects.select_related("author")
for book in books:
    print(book.author.name)  # no extra queries
```

Detect with Debug Toolbar, Silk, or logging SQL.

---

## 5. Auth, Sessions, Caching & Security

### How to create a custom authentication backend in Django

```python
# myapp/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get("email") or username
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def user_can_authenticate(self, user):
        return getattr(user, "is_active", True)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

```python
# settings.py
AUTHENTICATION_BACKENDS = [
    "myapp.backends.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

---

### What is Django session framework?

Sessions persist data across requests for a given client (browser).

- Session ID stored in cookie (`sessionid`)
- Session data stored in backend: **DB**, **cache**, **file**, **signed cookie**

```python
# settings
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# usage
request.session["cart_id"] = 42
cart = request.session.get("cart_id")
del request.session["cart_id"]
request.session.flush()  # logout-style clear
```

Requires `SessionMiddleware` and `django.contrib.sessions` in `INSTALLED_APPS`.

---

### Explain Caching

Django cache framework supports multiple backends: LocMem, Memcached, **Redis**, DB, file.

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "TIMEOUT": 300,
        "KEY_PREFIX": "myapp",
    }
}
```

**Levels:**
1. **Per-site** — `UpdateCacheMiddleware` / `FetchFromCacheMiddleware`
2. **Per-view** — `@cache_page(60 * 5)`
3. **Template fragment** — `{% cache 500 sidebar %}`
4. **Low-level** — `cache.set` / `cache.get`

```python
from django.core.cache import cache

cache.set("user:1", user_data, timeout=300)
data = cache.get("user:1")
cache.delete("user:1")

# get_or_set
data = cache.get_or_set("home:stats", compute_stats, 60)
```

Also: cache QuerySet results carefully (don’t cache unevaluated QS; cache lists/dicts).

---

### How to Secure Django App Before Production

Checklist:

```python
DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # never hardcode
ALLOWED_HOSTS = ["api.example.com"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = ["https://example.com"]

# If behind proxy/load balancer
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

Also:
- Use HTTPS everywhere
- Strong DB passwords / secrets in env / vault
- Least-privilege DB user
- Keep Django/deps updated
- Auth + permissions + throttling on APIs
- Restrict CORS origins
- Disable browsable API in prod (or lock it down)
- Run `python manage.py check --deploy`

---

### Explain Django reusability with other code / apps

Django promotes reusable **apps**:

1. Keep apps focused (`users`, `billing`, `catalog`)
2. Use abstract `BaseModel`, mixins, utils packages
3. Publish internal packages / install via pip
4. Avoid circular imports; depend on interfaces
5. Settings via `AppConfig`, not hardcoded secrets
6. Reuse with DRF serializers/viewsets across projects
7. Templates / static namespaced per app

A reusable app should work when listed in `INSTALLED_APPS` with minimal coupling to project-specific code.

---

## 6. Celery, Logging & Management Commands

### Explain Celery Integration

**Celery** = distributed task queue for async/background jobs (emails, reports, webhooks).

**Stack:** Django → Celery worker → Broker (Redis/RabbitMQ) → Result backend (optional)

```bash
pip install celery redis
```

```python
# myproject/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
app = Celery("myproject")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

```python
# myproject/__init__.py
from .celery import app as celery_app
__all__ = ("celery_app",)
```

```python
# settings.py
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
CELERY_TASK_ALWAYS_EAGER = False  # True only in tests
```

```python
# app/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    try:
        ...
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

```python
# call it
send_welcome_email.delay(user.id)
send_welcome_email.apply_async(args=[user.id], countdown=10)
```

```bash
celery -A myproject worker -l info
celery -A myproject beat -l info   # scheduled tasks
```

---

### Why use a Management Command in Django?

Custom CLI tasks under `app/management/commands/`:

**Uses:** one-off data migrations, cron jobs, imports/exports, cache warmup, health checks, seeding.

```python
# myapp/management/commands/expire_trials.py
from django.core.management.base import BaseCommand
from myapp.models import Subscription

class Command(BaseCommand):
    help = "Expire trial subscriptions"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        qs = Subscription.objects.filter(status="trial", ...)
        if options["dry_run"]:
            self.stdout.write(f"Would expire {qs.count()}")
            return
        updated = qs.update(status="expired")
        self.stdout.write(self.style.SUCCESS(f"Expired {updated}"))
```

```bash
python manage.py expire_trials --dry-run
```

Better than ad-hoc scripts: project settings, ORM, DB connections, logging all available.

---

### How to use pagination in Django?

**Django views:**

```python
from django.core.paginator import Paginator

def article_list(request):
    paginator = Paginator(Article.objects.all(), 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "list.html", {"page": page})
```

**DRF:**

```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
```

```python
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
```

---

## 7. DRF / REST API

### Different HTTP methods supported by REST

| Method | Purpose | Idempotent? |
|--------|---------|-------------|
| **GET** | Read resource(s) | Yes |
| **POST** | Create / action | No |
| **PUT** | Full replace | Yes |
| **PATCH** | Partial update | No* |
| **DELETE** | Remove | Yes |
| **HEAD** | Headers only | Yes |
| **OPTIONS** | Allowed methods / CORS preflight | Yes |

\*PATCH is often treated as non-idempotent depending on semantics.

---

### API Versioning in Django REST Framework

DRF strategies:
- `URLPathVersioning` → `/api/v1/users/`
- `NamespaceVersioning`
- `AcceptHeaderVersioning` → `Accept: application/json; version=1.0`
- `HostNameVersioning` → `v1.api.example.com`
- `QueryParameterVersioning` → `?version=v1`

```python
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1", "v2"],
}

# urls
path("api/<str:version>/", include("api.urls")),
```

In views: branch on `request.version`. Keep old versions until clients migrate.

---

### Different authentication methods in DRF

| Method | Use case |
|--------|----------|
| **SessionAuthentication** | Browser / same-site + CSRF |
| **BasicAuthentication** | Simple / legacy (HTTPS only) |
| **TokenAuthentication** | Simple API tokens (`Authorization: Token …`) |
| **JWT** (SimpleJWT) | Stateless mobile/SPA APIs |
| **RemoteUserAuthentication** | Auth handled by web server |
| **Custom** | API keys, OAuth2 (via packages like `django-oauth-toolkit`) |

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}
```

---

### CORS

**CORS (Cross-Origin Resource Sharing)** — browser security: frontend on `https://app.com` calling `https://api.com` needs explicit allowance.

Use `django-cors-headers`:

```bash
pip install django-cors-headers
```

```python
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # high in the list
    "django.middleware.common.CommonMiddleware",
    ...
]

CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True
# Avoid CORS_ALLOW_ALL_ORIGINS = True in production
```

---

### Model Serializers

```python
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "price"]
        read_only_fields = ["id"]
```

Auto-generates fields + validators from the model; implements `create` / `update`.

---

### Nested Serializers

```python
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name"]

class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), source="author", write_only=True
    )

    class Meta:
        model = Book
        fields = ["id", "title", "author", "author_id"]
```

Writable nested creates need custom `create`/`update`. Prefer IDs for writes; nest for reads. Watch N+1 — use `select_related`/`prefetch_related` in the viewset queryset.

---

### ViewSets vs Generic Views

| | Generic APIView classes | ViewSets |
|--|-------------------------|----------|
| Examples | `ListCreateAPIView`, `RetrieveUpdateDestroyAPIView` | `ModelViewSet`, `ReadOnlyModelViewSet` |
| Routing | Manual `path()` per view | `DefaultRouter` / `SimpleRouter` |
| Actions | Fixed per class | `list`, `create`, `retrieve`, `update`, `partial_update`, `destroy` + `@action` |
| Best when | Few custom endpoints | Full CRUD resources |

```python
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related("author")
    serializer_class = BookSerializer

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        book = self.get_object()
        book.is_published = True
        book.save()
        return Response({"status": "published"})
```

---

### Custom Permissions

```python
from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.owner_id == request.user.id

class IsPythonDeptStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, "department", None) == "Python"
        )
```

```python
class BookViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
```

---

### Throttling

Rate-limits requests to prevent abuse.

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "withdrawals": "10/hour",
    },
}

class ATMWithdrawView(APIView):
    throttle_scope = "withdrawals"
```

Use a **shared cache** (Redis) so limits work across multiple workers. Over limit → HTTP **429**.

---

## 8. API Observability

### What is API Observability? What are the 4 pillars?

**API Observability** = ability to understand API behavior in production from external outputs (not by guessing or SSH debugging).

**Four pillars (MELT):**

| Pillar | Meaning | Examples |
|--------|---------|----------|
| **Metrics** | Numeric time-series | request rate, latency p95, error %, CPU, DB pool usage |
| **Events** | Discrete notable occurrences | deploy, config change, spike alert |
| **Logs** | Timestamped records of what happened | access logs, error stack traces, audit trails |
| **Traces** | Request journey across services | distributed trace IDs through API → Celery → DB |

Together they answer: *Is it broken? Where? Why? Who is impacted?*

Tools often used with Django: OpenTelemetry, Prometheus + Grafana, Sentry, ELK/OpenSearch, Jaeger/Tempo, Datadog.

---

## 9. Django Coding Questions

### Middleware coding scenarios

Common interview uses of middleware:
- Ensure auth/permissions before views
- Log requests/responses
- Measure request timing / performance
- Block IPs
- Compress responses
- Add/modify headers
- Rate limiting
- Force HTTPS / security headers
- API version routing
- Log time taken per request

#### Custom middleware that logs time taken

```python
import logging
import time

logger = logging.getLogger(__name__)

class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration = time.perf_counter() - start
        logger.info("%s %s took %.3fs", request.method, request.path, duration)
        response["X-Request-Duration"] = f"{duration:.3f}"
        return response
```

#### IP block middleware

```python
from django.http import HttpResponseForbidden

BLOCKED = {"1.2.3.4", "5.6.7.8"}

class BlockIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        if ip in BLOCKED:
            return HttpResponseForbidden("Forbidden")
        return self.get_response(request)
```

---

### REST: Unique blog title validation in serializer

```python
from rest_framework import serializers
from .models import BlogPost

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ["id", "title", "body"]

    def validate_title(self, value):
        qs = BlogPost.objects.filter(title__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Title must be unique.")
        return value
```

(Alternatively `UniqueValidator` on the field, or `unique=True` on the model field.)

---

### REST: ATM withdrawal API

Rules: `atm_pin` = 6 digits; `amount` multiple of 100 and `< 1000`.

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db import transaction
from django.db.models import F

class ATMWithdrawSerializer(serializers.Serializer):
    atm_pin = serializers.RegexField(regex=r"^\d{6}$", max_length=6, min_length=6)
    amount = serializers.IntegerField(min_value=100, max_value=900)

    def validate_amount(self, value):
        if value % 100 != 0:
            raise serializers.ValidationError("Amount must be a multiple of 100.")
        if value >= 1000:
            raise serializers.ValidationError("Amount must be less than 1000.")
        return value

class ATMWithdrawView(APIView):
    def post(self, request):
        ser = ATMWithdrawSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        pin = ser.validated_data["atm_pin"]
        amount = ser.validated_data["amount"]

        try:
            with transaction.atomic():
                account = (
                    Account.objects
                    .select_for_update()
                    .get(atm_pin=pin, is_active=True)
                )
                if account.balance < amount:
                    return Response(
                        {"detail": "Insufficient funds"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                Account.objects.filter(pk=account.pk).update(
                    balance=F("balance") - amount
                )
                account.refresh_from_db(fields=["balance"])
        except Account.DoesNotExist:
            return Response(
                {"detail": "Invalid PIN"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {"withdrawn": amount, "balance": account.balance},
            status=status.HTTP_200_OK,
        )
```

---

### Quick cheat sheet

| Topic | One-liner |
|-------|-----------|
| MVT | Model-View-Template |
| WSGI | Sync Python web interface; uWSGI is a server |
| Mixin | Reusable behavior class |
| Manager | Entry point to DB queries (`objects`) |
| Q | Complex AND/OR/NOT filters |
| F | DB-side field reference / atomic updates |
| select_related | JOIN (FK/O2O) |
| prefetch_related | Extra queries (reverse/M2M) |
| atomic | All-or-nothing DB transaction |
| Celery | Async task queue |
| Throttling | Rate limiting (429) |
| Observability | Metrics, Events, Logs, Traces |

---

*Sources: Django docs (ORM, databases, migrations, auth), DRF docs (versioning, auth, throttling), and production practices (CORS, Celery, pooling).*
