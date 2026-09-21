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

## Django

#### Q1. To cache your entire site for an application in Django, you add all except which of these settings?

- [ ] django.middleware.common.CommonMiddleware
- [ ] django.middleware.cache.UpdateCacheMiddleware
- [ ] django.middleware.cache.FetchFromCacheMiddleware
- [x] django.middleware.cache.AcceleratedCacheMiddleware

**Reference:**
Django comes with a robust cache system that lets you save dynamic pages, so they don’t have to be computed for each request. For convenience, Django offers cache with different granularity — from entire website to pages to part of pages to DB query results to any objects in memory. Cache middleware. If enabled, each Django-powered page will be cached based on URL.

#### Q2. In which programming language is Django written?

- [ ] C++
- [ ] Java
- [x] Python
- [ ] Ruby

#### Q3. To automatically provide a value for a field, or to do validation that requires access to more than a single field, you should override the `___` method in the `___` class.

- [ ] validate(); Model
- [ ] group(); Model
- [ ] validate(); Form
- [x] clean(); Field

#### Q4. A client wants their site to be able to load "Rick & Morty" episodes by number or by title—e.g., shows/3/3 or shows/picklerick. Which URL pattern do you recommend?

- [ ] A

```python
url(r'shows/<int:season>/<int:episode>/', views.episode_number),
url(r'shows/<slug:episode_name>/', views.episode_name)
```

- [x] B

```python
path('shows/<int:season>/<int:episode>/', views.episode_number),
path('shows/<slug:episode_name>/', views.episode_name)
```

- [ ] C

```python
path('shows/<int:season>/<int:episode>', views.episode_number),
path('shows/<slug:episode_name>/', views.episode_number)
```

- [ ] D

```python
url(r'^show/(?P<season>[0-9]+)/(?P<episode>[0-9]+)/$', views.episode_number),
url(r'^show/(?P<episode_name>[\w-]+)/', views.episode_name
```

#### Q5. How do you determine at startup time if a piece of middleware should be used?

- [x] Raise MiddlewareNotUsed in the **init** function of your middleware.
- [ ] Implement the not_used method in your middleware class.
- [ ] List the middleware beneath an entry of django.middleware.IgnoredMiddleware.
- [ ] Write code to remove the middleware from the settings in [app]/**init**.py.

#### Q6. How do you turn off Django’s automatic HTML escaping for part of a web page?

- [ ] Place that section between paragraph tags containing the autoescape=off switch.
- [ ] Wrap that section between { percentage mark autoescape off percentage mark} and {percentage mark endautoescape percentage mark} tags.
- [ ] Wrap that section between {percentage mark autoescapeoff percentage mark} and {percentage mark endautoescapeoff percentage mark} tags.
- [x] You don't need to do anything—autoescaping is off by default.

#### Q7. Which step would NOT help you troubleshoot the error "django-admin: command not found"?

- [ ] Check that the bin folder inside your Django directory is on your system path.
- [ ] Make sure you have activated the virtual environment you have set up containing Django.
- [ ] Check that you have installed Django.
- [x] Make sure that you have created a Django project.

#### Q8. Every time a user is saved, their quiz_score needs to be recalculated. Where might be an ideal place to add this logic?

- [ ] template
- [x] model
- [ ] database
- [ ] view

#### Q9. What is the correct way to begin a class called "Rainbow" in Python?

- [ ] Rainbow {}
- [ ] export Rainbow:
- [x] class Rainbow:
- [ ] def Rainbow:

#### Q10. You have inherited a Django project and need to get it running locally. It comes with a requirements.txt file containing all its dependencies. Which command should you use?

- [ ] django-admin startproject requirements.txt
- [ ] python install -r requirements.txt
- [x] pip install -r requirements.txt
- [ ] pip install Django

#### Q11. Which best practice is NOT relevant to migrations?

- [x] To make sure that your migrations are up to date, you should run updatemigrations before running your tests.
- [ ] You should back up your production database before running a migration.
- [ ] Your migration code should be under source control.
- [ ] If a project has a lot of data, you should test against a staging copy before running the migration on production.

#### Q12. What will this URL pattern match? url(r'^\$', views.hello)

- [ ] a string beginning with the letter Ra string beginning with the letter R
- [x] an empty string at the server root
- [ ] a string containing ^ and $a string containing ^ and $
- [ ] an empty string anywhere in the URLan empty string anywhere in the URL

#### Q13. What is the typical order of an HTTP request/response cycle in Django?

- [x] URL > view > template
- [ ] form > model > view
- [ ] template > view > model
- [ ] URL > template > view > model

#### Q14. Django's class-based generic views provide which classes that implement common web development tasks?

- [ ] concrete
- [ ] thread-safe
- [x] abstract
- [ ] dynamic

#### Q15. Which skills do you need to maintain a set of Django templates?

- [ ] template syntax
- [x] HTML and template syntax
- [ ] Python, HTML, and template syntax
- [ ] Python and template syntax

#### Q16. How would you define the relationship between a star and a constellation in a Django model?

- [x] A

```python
class Star(models.Model):
name = models.CharField(max_length=100)
class Constellation(models.Model):
stars = models.ManyToManyField(Star)
```

- [ ] B

```python
class Star(models.Model):
constellation = models.ForeignKey(Constellation, on_delete=models.CASCADE)
class Constellation(models.Model):
stars = models.ForeignKey(Star, on_delete=models.CASCADE)
```

- [ ] C

```python
class Star(models.Model):
name = models.CharField(max_length=100)
class Constellation(models.Model):
stars = models.OneToManyField(Star)
```

- [ ] D

```python
class Star(models.Model):
constellation = models.ManyToManyField(Constellation)
class Constellation(models.Model):
name = models.CharField(max_length=100)
```

#### Q17. Which is NOT a valid step in configuring your Django 2.x instance to serve up static files such as images or CSS?

- [x] In your urls file, add a pattern that includes the name of your static directory.
- [ ] Create a directory named static inside your app directory.
- [ ] Create a directory named after the app under the static directory, and place static files inside.
- [ ] Use the template tag {percentage mark load static percentage mark}.

#### Q18. What is the correct way to make a variable available to all of your templates?

- [ ] Set a session variable.
- [ ] Use a global variable.
- [ ] Add a dictionary to the template context.
- [x] Use RequestContext.

#### Q19. Should you create a custom user model for new projects?

- [ ] No. Using a custom user model could break the admin interface and some third-party apps.
- [x] Yes. It is easier to make changes once it goes into production.
- [ ] No. Django's built-in models.User class has been tried and tested—no point in reinventing the wheel.
- [ ] Yes, as there is no other option.

#### Q20. You want to create a page that allows editing of two classes connected by a foreign key (e.g., a question and answer that reside in separate tables). What Django feature can you use?

- [x] actions
- [ ] admin
- [ ] mezcal
- [ ] inlines

#### Q21. Why are QuerySets considered "lazy"?

- [ ] The results of a QuerySet are not ordered.
- [x] QuerySets do not create any database activity until they are evaluated.
- [ ] QuerySets do not load objects into memory until they are needed.
- [ ] Using QuerySets, you cannot execute more complex queries.

#### Q22. You receive a `MultiValueDictKeyError` when trying to access a request parameter with the following code: request.GET['search_term']. Which solution will NOT help you in this scenario?

- [x] Switch to using POST instead of GET as the request method.
- [ ] Make sure the input field in your form is also named "search_term".
- [ ] Use MultiValueDict's GET method instead of hitting the dictionary directly like this: request.GET.get('search_term', '').
- [ ] Check if the search_term parameter is present in the request before attempting to access it.

#### Q23. Which function of Django's Form class will render a form's fields as a series of <p> tags?

- [ ] show_fields()
- [x] as_p()
- [ ] as_table()
- [ ] fields()

#### Q24. You have found a bug in Django and you want to submit a patch. Which is the correct procedure?

- [ ] Fork the Django repository GitHub.
- [ ] Submit a pull request.
- [x] all of these answers.
- [ ] Run Django's test suite.

#### Q25. Django supplies sensible default values for settings. In which Python module can you find these settings?

- [ ] `django.utils.default_settings.py`
- [ ] `django.utils.global_settings.py`
- [ ] `django.conf.default_settings.py`
- [x] `django.conf.global_settings.py`

#### Q26. Which variable name is best according to PEP 8 guidelines?

- [ ] numFingers
- [ ] number-of-Fingers
- [x] number_of_fingers
- [ ] finger_num

#### Q27. A project has accumulated 500 migrations. Which course of action would you pursue?

- [ ] Manually merge your migration files to reduce the number
- [ ] Don't worry about the number
- [ ] Try to minimize the number of migrations
- [x] Use squashmigrations to reduce the number

#### Q28. What does an F() object allow you when dealing with models?

- [x] perform db operations without fetching a model object
- [ ] define db transaction isolation levels
- [ ] use aggregate functions more easily
- [ ] build reusable QuerySets

#### Q29. Which is not a Django field type for holding integers?

- [ ] SmallIntegerField
- [x] NegativeIntegerField
- [ ] BigAutoField
- [ ] PositiveIntegerField

#### Q30. Which will show the currently installed version?

- [ ] print (django.version)
- [ ] import django django.getVersion()
- [x] import django django.get_version()
- [ ] python -c django --version

#### Q31. You should use the http method `___` to read data and `___` to update or create data

- [ ] READ; WRITE
- [x] GET; POST
- [ ] POST; GET
- [ ] GET; PATCH

#### Q32. When should you employ the POST method over GET for submitting data?

- [ ] when efficiency is important
- [ ] when you want the data to be cached
- [ ] when you want to use your browser to help with debugging
- [x] when the data in the form may be sensitive

#### Q33. When to use the Django sites framework?

- [x] if your single installation powers more than one site
- [ ] if you need to serve static as well as dynamic content
- [ ] if you want your app have a fully qualified domain name
- [ ] if you are expecting more than 10.000 users

#### Q34. Which infrastructure do you need:

`title=models.charfield(max_length=100, validators=[validate_spelling])`

- [ ] inizialized array called validators
- [x] a validators file containing a function called validate_spelling imported at the top of model
- [ ] a validators file containing a function called validate imported at the top of model
- [ ] spelling package imported at the top of model

#### Q35. What decorator is used to require that a view accepts only the get and head methods?

- [x] require_safe()
- [ ] require_put()
- [ ] require_post()
- [ ] require_get()

#### Q36. How would you define the relation between a book and an author - book has only one author.

```python
class Author (models.model):
book=models.foreignkey(Book,on_delete=models.cascade)
class Book(models.model):
name=models.charfield(max_length=100)
```

- [ ] A

```python
class Author (models.model):
name=models.charfield(max_length=100)
class Book(models.model):
author=models.foreignkey(Author,on_delete=models.cascade)
```

- [x] B

```python
class Author (models.model):
name=models.charfield(max_length=100)
class Book(models.model):
author=models.foreignkey(Author)
```

- [ ] C

```python
class Author (models.model):
name=models.charfield(max_length=100)
class Book(models.model):
author=models.foreignkey(Author,on_delete=models.cascade)
```

- [ ] D

```python
class Author (models.model):
name=models.charfield(max_length=100)
class Book(models.model):
author=Author.name
```

#### Q37. What is a callable that takes a value and raises an error if the value fails?

- [x] validator
- [ ] deodorizer
- [ ] mediator
- [ ] regular expression

#### Q38. To secure an API endpoint, making it accessible to registered users only, you can replace the rest_framework.permissions.allowAny value in the default_permissions section of your settings.py to

- [ ] rest_framework.permissions.IsAdminUser
- [x] rest_framework.permissions.IsAuthenticated
- [ ] rest_framework.permissions.IsAuthorized
- [ ] rest_framework.permissions.IsRegistered

#### Q39. Which command would you use to apply a migration?

- [ ] makemigration
- [ ] update_db
- [ ] applymigration
- [x] migrate

#### Q40. Which type of class allows QuerySets and model instances to be converted to native Python data types for use in APIs?

- [ ] objectwriters
- [x] serializers
- [ ] picklers
- [ ] viewsets

#### Q41. How should the code end?

```python
{ percentage if spark >= 50 percentage }
Lots of spark
{percentage elif spark == 42 percentage}
```

- [ ] { percentage else percentage}
- [x] {percentage endif percentage}
- [ ] Nothing needed
- [ ] {percentage end percentage}

#### Q42. Which code block will create a serializer?

```python
from rest_framework import serializers
from .models import Planet
```

- [x] A

```python
class PlanetSerializer(serializers.ModelSerializer):
class Meta:
model=Planet
fields=('name','position', 'mass', 'rings')
```

- [ ] B

```python
from rest_framework import serializers
from .models import Planet
class PlanetSerializer():
class Meta:
fields=('name','position', 'mass', 'rings')
model=Planet
```

- [ ] C

```python
from django.db import serializers
from .models import Planet
class PlanetSerializer(serializers.ModelSerializer):
fields=('name','position', 'mass', 'rings')
model=Sandwich
```

- [ ] D

```python
from django.db import serializers
from .models import Planet
class PlanetSerializer(serializers.ModelSerializer):
class Meta:
fields=('name')
model=Planet
```

#### Q43. Which class allows you to automatically create a Serializer class with fields and validators that correspond to your model's fields?

- [x] ModelSerializer
- [ ] Model
- [ ] DataSerializer
- [ ] ModelToSerializer

#### Q44. Which command to access the built-in admin tool for the first time?

- [ ] django-admin setup
- [ ] django-admin runserver
- [ ] python manage.py createuser
- [x] python manage.py createsuperuser

#### Q45. Virtual environments are for managing dependencies. Which granularity works best?

- [x] you should set up a new virtualenv for each Django project
- [ ] They should not be used
- [ ] Use the same venv for all your Django work
- [ ] Use a new venv for each Django app

#### Q46. What executes various Django commands such as running a webserver or creating an app?

- [ ] migrate.py
- [ ] wsgi.py
- [x] manage.py
- [ ] runserver

#### Q47. What do Django best practice suggest should be "fat"?

- [x] models
- [ ] controllers
- [ ] programmers
- [ ] clients

#### Q48. Which is not part of Django's design philosophy?

- [ ] Loose Coupling
- [ ] Less Code
- [ ] Fast Development
- [x] Implicit over explicit

#### Q49. What is the result of this template code?

{{"live long and prosper"|truncatewords:3}}

- [x] live long and ...
- [ ] live long and
- [ ] a compilation error
- [ ] liv

#### Q50. When does this code load data into memory?

```
1 sandwiches = Sandwich.objects.filter(is_vegan=True)
2 for sandwich in sandwiches:
3   print(sandwich.name + " - " + sandwich.spice_level)
```

- [ ] line 1
- [x] It depends on how many results return by query.
- [ ] It depends on cache.
- [ ] line 2

#### Q51. You are building a web application using a React front end and a Django back end. For what will you need to provision?\*\*

- [ ] an NGINX web server
- [ ] a NoSQL database
- [ ] a larger hard drive
- [x] CORS middleware

#### Q52. To expose an existing model via an API endpoint, what do you need to implement?\*\*

- [ ] an HTTP request
- [ ] a JSON object
- [ ] a query
- [x] a serializer

#### Q53. How would you stop Django from performing database table creation or deletion operations via migrations for a particular model?

- [ ] Run the `migrate` command with `--exclude=[model_name]`.
- [ ] Move the model definition from `models.py` into its own file.
- [x] Set `managed=False` inside the model.
- [ ] Don't run the `migrate` command.

#### Q54. what method can you use to check if form data has changed when using a form instance?

- [x] has_changed()
- [ ] its_changed()
- [ ] has_updated()
- [ ] None of This

#### Q55. What is WSGI?

- [ ] a server
- [x] an interface specifications
- [ ] a Python module
- [ ] a framework

Reference link:- https://wsgi.tutorial.codepoint.net/intro

#### Q56. Which generic view should be used for displaying the titles of all Django Reinhardt's songs?

- [ ] DetailView
- [ ] TittleView
- [ ] SongView
- [x] ListView

#### Q57. Which statement is most accurate, regarding using the default SQLite database on your local/development machine but Postgres in production

- [x] There's less chance of introducing bugs since SQLite already works out the box
- [ ] It's fine, you just need to keep both instances synchronized
- [ ] It's a bad idea and could lead to issues down the road
- [ ] It's the most efficient way to build a project

#### Q58. Why might you want to write a custom model Manager?

- [ ] to perform database queries
- [ ] to set up a database for testing
- [x] to modify the initial QuerySet that the Manager returns
- [ ] to filter the results that a database query returns

#### Q59. In Django, what are used to customize the data that is sent to the templates?

- [ ] models
- [x] views
- [ ] forms
- [ ] serializers

#### Q60. To complete the conditional, what should this block of code end with?

```shell
% if sparles >= 50 %
  Lots of sparkles!
% elif sparkles == 42 %
  The answer to life, the universe, and everything!
```

- [x] `% endif %`
- [ ] Nothing else is needed.
- [ ] `% end%`
- [ ] `% else %`

#### Q61. When should you employ the POST method over the GET method for submitting data from a form?

- [x] when the data in the form may be sensitive
- [ ] when you want the data to be cached
- [ ] when you want to use your browser to help with debugging
- [ ] when efficiency is important

#### Q62. What is a callable that takes a value and raises an error if the value fails to meet some criteria?

- [ ] mediator
- [x] validator
- [ ] regular expression
- [ ] deodorizer

#### Q63. You are uploading a file to Django from a form and you want to save the received file as a field on a model object. You can simply assign the file object from**\_to a field of type\_\_**in the model.

- [ ] request.META; FileField
- [ ] request.FILES; BLOBField
- [x] request.FILES; FileField
- [ ] request.META.Files; CLOBField

#### Q64. What python module might be used to store the current state of a Django model in a file?

- [x] pickle
- [ ] struct
- [ ] marshal
- [ ] serialize

#### Q65. To add a new app to an existing Django project, you must edit the **_ section of the _** file.

- [ ] ALLOWED_HOSTS; settings.py
- [ ] APPS; manage.py
- [x] INSTALLED_APPS; settings.py
- [ ] TEMPLATES; urls.py

#### Q66. Which is not a third-party package commonly used for authentication?

- [ ] django-guardian
- [ ] django-rest-auth
- [ ] authtoken
- [x] django-rest-framework-jwt

#### Q67. Which function in the django.urls package can help you avoid hardcoding URLS by generating a URL given the name of a view?

- [ ] get_script_prefix()
- [ ] redirect()
- [x] reverse()
- [ ] resolve()

#### Q68. Which is Fictional HTTP request method?

- [ ] POST
- [ ] PUT
- [x] PAUSE
- [ ] PATCH

#### Q69. Which helper function is not provided as a part of django.shortcuts package? ref-

- [x] render_to_request()
- [ ] render()
- [ ] redirect()
- [ ] get_object_or_404()

[Reference](https://docs.djangoproject.com/en/4.0/topics/http/shortcuts/#:~:text=The%20package%20django.,controlled%20coupling%20for%20convenience's%20sake)

#### Q70. Which is a nonstandard place to store templates?

- [x] at the root level of a project
- [ ] inside the application
- [ ] in the database
- [ ] on Github

#### Q71. If you left the 8080 off the command python manage.py runserver 8080 what port would Django use as default?

- [x] 8080
- [ ] 80
- [ ] 8000
- [ ] It would fail to start

#### Q72. Which statement about Django apps is false?

- [x] A Django app is the top-level container for a web application powered by Django.
- [ ] Django apps are small libraries designed to represent a single aspect of a project.
- [ ] Each Django app should do one thing, and one thing alone.
- [ ] A Django project is made up of many apps.

#### Q73. Which characters are illegal in template variable names?

- [ ] underscores.
- [ ] uppercase letters.
- [x] punctuation marks .
- [ ] numbers.

[Reference](https://docs.djangoproject.com/en/4.1/ref/templates/language/#:~:text=Variable%20names%20consist%20of%20any,may%20not%20be%20a%20number.)

#### Q74. Which is not a valid closing template tag?

- [ ] `% endautoescape %`
- [x] `% endifempty %`
- [ ] `% endcomment %`
- [ ] `% endfilter %`

#### Q75. When would you need to use the reverse_lazy utility function instead of reverse?

- [ ] when you want to provide a reverse URL as a default value for a parameter in a function's signature
- [x] all of the these answers
- [ ] when you want to provide a reverse URL as the url attribute of a class-based generic view
- [ ] when you want to provide a URL to a decorator, such as the login_url argument for the permission_required() decorator

#### Q76. What is the purpose of the \_\_init\_\_.py file?

- [ ] to extend the set of modules found in a package
- [ ] to allow compiled modules from different releases and different versions of Python to coexist
- [ ] to initialize project settings
- [x] to declare the directory contents as a Python module

[Reference](<https://docs.djangoproject.com/en/4.1/ref/urlresolvers/#:~:text=reverse_lazy()&text=It%20is%20useful%20for%20when,a%20generic%20class%2Dbased%20view>)

#### Q77. What python package can be used to edit numbers into more readable form like "1200000" to "1.2 million"?

- [ ] black
- [ ] puffer
- [ ] pitch
- [x] humanize

#### Q78. Where would you find the settings.py file?

- [x] \[projectname\]/settings.py
- [ ] \[projectname\]/\[projectname\]/settings.py
- [ ] \[PYTHON_ROOT\]/settings.py
- [ ] \[DJANGO_ROOT]/settings.py

#### Q79. What would you write to define the relationship between a book and an author--assuming a book has only one author-in a Django model?

- [x] A

```python
class Author (models.Model):
  name = models. CharField (max_length=100)
class Book(models .Model):
  author = models. ForeignKey (Author, on_delete=models. CASCADE)
```

- [ ] B

```python
class Author (models.Model):
  name = models. CharField(max length=100)
class Book(models .Model):
  author = models. ForeignKey (Author)
```

- [ ] C

```python
class Author (models .Model):
  name = models.CharField (max_length=100)
class Book (models .Author) :
  author = Author. name
```

- [ ] D

```python
class Author (models. Model):
  book = models. ForeignKey (Book, on_delete=models.CASCADE)
class Book(models.Model):
  name = models. CharField (max length=100)
```

#### Q80. What method can you use to check if form data has been changed when using a Form instance?

- [x] changed_data()
- [ ] has changed()
- [ ] has_updated()
- [ ] is_modified()

#### Q81. Which statement is most accurate, regarding using the default SQLite database on your local/development machine but Postgres in production?

- [ ] It's the most efficient way to build a project
- [ ] There's less chance of introducing bugs since SQLite already works out of the box
- [ ] It's a bad idea and could lead to issues down the road
- [x] It's fine, you just need to keep both instances synchronized

#### Q82. How does Django handle URL routing?

- [ ] by using classes
- [ ] by using functiones
- [x] by using regular expressions
- [ ] by using fixed path

#### Q83. What is the purpose of Django's middleware?

- [ ] To define the database schema
- [ ] To manage URL routing
- [x] To handle HTTP requests and responses globally
- [ ] To create user interfaces

[Reference](https://medium.com/scalereal/everything-you-need-to-know-about-middleware-in-django-2a3bd3853cd6)

#### Q84. Which of the following is true about Django's Object-Relational Mapping (ORM)?

- [ ] It's used to define URL routing in a Django application.
- [x] It allows you to query the database using Python code.
- [ ] It's used to define the structure of HTML templates.
- [ ] It's responsible for managing user authentication.

#### Q85. Which of the following is true about Django's "many-to-many" field in a model?

- [ ] It's used to define a one-to-one relationship between two models.
- [ ] It creates a foreign key relationship between two models.
- [x] It allows multiple objects to be associated with each other.
- [ ] It enforces unique constraints on a field.

#### Q86. Django's class-based generic views provide which classes that implement common web development tasks?

- [ ] concrete
- [ ] thread-safe
- [x] abstract
- [ ] dynamic

#### Q87. Which skills do you need to maintain a set of Django templates?

- [ ] template syntax
- [x] HTML and template syntax
- [ ] Python, HTML, and template syntax
- [ ] Python and template syntax

#### Q88. Which is a nonstandard place to store templates?

- [x] at the root level of a project
- [ ] inside the application
- [ ] in the database
- [ ] on Github

#### Q89. If you left the 8080 off the command python manage.py runserver 8080 what port would Django use as default?

- [x] 8080
- [ ] 80
- [ ] 8000
- [ ] It would fail to start

#### Q90. What is the purpose of Django's Object-Relational Mapping (ORM)?

- [ ] To define URL routing in a Django application.
- [ ] To handle HTTP requests and responses globally.
- [x] To map Python objects to database tables and simplify database operations.
- [ ] To create user interfaces.

#### Q91. In Django, what does the term "migration" refer to?

- [ ] A change in URL routing configuration.
- [x] The process of propagating changes you make to your models (adding a field, deleting a model, etc.) into your database schema.
- [ ] A way to define custom middleware.
- [ ] The process of creating HTML templates for your application.

#### Q92. What is the purpose of Django's "context" in the context of rendering templates?

- [x] To pass data from your views to your templates so that the data can be rendered dynamically.
- [ ] To define URL patterns for your application.
- [ ] To manage HTTP requests and responses.
- [ ] To create user interfaces.

#### Q93. What does the Django `QuerySet` class represent?

- [ ] A Python class used for defining URL routing in Django.
- [ ] A class for managing HTTP requests and responses.
- [x] A database query made by Django, represented in Python.
- [ ] A class for defining HTML templates.

#### Q94. In Django, what is the purpose of the "collectstatic" management command?

- [ ] To collect user data for analytics.
- [ ] To collect database records from multiple sources.
- [x] To collect all static files (CSS, JavaScript, images) from each of your applications into a single location.
- [ ] To collect logs for debugging purposes.

#### Q95. What is the Django Admin site used for?

- [ ] To manage user authentication.
- [ ] To define URL routing for Django applications.
- [x] To provide an automatically generated admin interface for your models.
- [ ] To write and run database queries.

#### Q96. What does Django's "middleware" refer to?

- [ ] A way to create user interfaces.
- [ ] A database query in Django.
- [x] A way to process HTTP requests and responses globally before they reach the view or after they leave the view.
- [ ] A way to configure URL routing in Django.

#### Q97. What is the primary purpose of Django's "migration files"?

- [x] To define and store changes to the database schema over time.
- [ ] To manage static files like CSS and JavaScript.
- [ ] To configure URL patterns.
- [ ] To create HTML templates.

#### Q98. Which authentication system does Django provide out of the box?

- [ ] OAuth 2.0
- [x] User authentication with built-in user models and views.
- [ ] JWT (JSON Web Tokens)
- [ ] SAML (Security Assertion Markup Language)

#### Q99. In Django, what does the "Model-View-Controller" (MVC) architectural pattern refer to?

- [ ] A pattern for defining URL routing.
- [ ] A pattern for creating HTML templates.
- [x] A pattern that divides the application into three interconnected components: Model, View, and Controller (Django often refers to it as MTV, Model-View-Template).
- [ ] A pattern for user authentication.

#### Q100. What is the purpose of Django's "templates"?

- [ ] To define database schema and model relationships.
- [x] To define the structure and layout of HTML pages to be served to the user.
- [ ] To configure URL patterns for your application.
- [ ] To store and serve static files like images and JavaScript.
