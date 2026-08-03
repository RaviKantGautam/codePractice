# API Design & DRF Interview Questions & Answers

> Interview prep covering REST API design, auth, observability, GraphQL comparison, and Django REST Framework coding patterns.

---

## Table of Contents

1. [REST API Design](#1-rest-api-design)
2. [Auth, CORS, HTTP & Throttling](#2-auth-cors-http--throttling)
3. [API Observability](#3-api-observability)
4. [Django REST Framework (DRF)](#4-django-rest-framework-drf)
5. [Coding: Contact Us API](#5-coding-contact-us-api)

---

## 1. REST API Design

### How do you ensure REST APIs are idempotent?

**Idempotent** = repeating the same request N times has the **same effect** on server state as doing it once (same final state; response may still be identical).

**By HTTP semantics:**
| Method | Idempotent? | Notes |
|--------|-------------|-------|
| `GET`, `HEAD`, `OPTIONS` | Yes | Safe + idempotent |
| `PUT` | Yes | Replace resource with same body → same result |
| `DELETE` | Yes | Delete once or thrice → resource gone |
| `POST` | **No** (by default) | Each call may create a new resource |
| `PATCH` | Often no | Depends on semantics |

**How to make non-idempotent ops safe (especially POST):**

1. **`Idempotency-Key` header** (Stripe-style)
   - Client sends unique key (UUID) per logical operation
   - Server stores key → response (Redis/DB, TTL ~24h)
   - Retries with same key return cached response — no double charge/create
2. **Natural unique keys** — `UNIQUE(order_id)` / upsert so duplicates are no-ops
3. **Idempotent resource design** — prefer `PUT /resources/{client-generated-id}` over blind `POST`
4. **Dedup tokens** — one-time tokens for form submissions

```http
POST /api/payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{"amount": 1000, "currency": "INR"}
```

---

### What are idempotent and safe methods in REST, and why are they important?

| Concept | Meaning | Methods |
|---------|---------|---------|
| **Safe** | No side effects on server state (read-only) | `GET`, `HEAD`, `OPTIONS` |
| **Idempotent** | Same effect if repeated | Safe methods + `PUT`, `DELETE` |

**Why important:**
- Clients/proxies can **retry** safely on timeouts (mobile networks)
- Caches and CDNs can store `GET` responses
- Load balancers / gateways can replay without corrupting data
- Prevents double-submit bugs (payments, orders)

---

### Paginated /search endpoint?

Design search as a **collection GET** with query params + pagination.

```http
GET /api/v1/products/search?q=laptop&category=electronics&min_price=1000&sort=-created_at&page=2&page_size=20
```

**Response shape (page-number style):**
```json
{
  "count": 153,
  "next": "https://api.example.com/api/v1/products/search?q=laptop&page=3",
  "previous": "https://api.example.com/api/v1/products/search?q=laptop&page=1",
  "results": [ ... ]
}
```

**Cursor-based (better for large/realtime data):**
```http
GET /api/v1/products/search?q=laptop&cursor=eyJpZCI6MTAwfQ&limit=20
```

**Best practices:**
- Index search fields / use full-text (Postgres `tsvector`, Elasticsearch)
- Cap `page_size` (e.g. max 100)
- Prefer **cursor** over deep `OFFSET`
- Validate/sanitize `q`; avoid SQL injection via ORM
- Return `400` for invalid filters
- Optionally support `fields=` sparse fieldsets

**DRF:**
```python
class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]
```

---

### How do you handle pagination in RESTful APIs?

| Strategy | Pros | Cons |
|----------|------|------|
| **Offset / page** (`?page=2&limit=20`) | Simple, jump to page N | Slow on deep pages; unstable if data shifts |
| **Cursor / keyset** (`?cursor=...`) | Stable, fast for infinite scroll | No random page access |
| **Link headers** (RFC 5988) | Clean body | Clients must read headers |

Always return total count *only if cheap*; otherwise omit or approximate. Include `next`/`previous` links.

---

### Versioning strategies?

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| **URL path** | `/api/v1/users` | Explicit, cache-friendly, easy routing | URL changes per version |
| **Query param** | `/api/users?version=1` | Easy to add | Easy to forget; caching messier |
| **Header** | `Accept: application/vnd.myapi.v1+json` | Clean URLs | Harder to test in browser |
| **Hostname** | `v1.api.example.com` | Strong isolation | DNS/ops overhead |

**Interview recommendation:** **URL path versioning** for public APIs (`/api/v1/`). Version from day one. Additive (non-breaking) changes stay in same version; breaking changes → new version.

**DRF:**
```python
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1", "v2"],
}
```

---

### Handling breaking changes in public APIs?

**Breaking** = removes/renames fields, changes types/semantics, tighter validation, auth changes that break old clients.

**Strategy:**
1. **Never break v1 in place** — ship `v2` alongside
2. **Deprecation policy** — announce, set sunset date, send `Deprecation` / `Sunset` headers
3. **Communicate** — changelog, email, developer portal
4. **Parallel run** — keep old version until traffic near zero
5. **Compatibility layer** — adapters that map old payloads → new services
6. **Consumer-driven contracts** / contract tests
7. Prefer **additive** evolution: new optional fields, new endpoints

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: <https://api.example.com/api/v2/orders>; rel="successor-version"
```

---

### Bulk upload API for CSV files?

**Pattern:**
1. `POST /api/v1/imports` with `multipart/form-data` file
2. Validate file type/size; store in object storage (S3) or temp
3. Create `ImportJob` row (`pending`)
4. Enqueue Celery/RQ task to parse CSV asynchronously
5. Return `202 Accepted` + job id
6. Client polls `GET /api/v1/imports/{id}` for status / error report

```http
POST /api/v1/contacts/bulk-upload
Content-Type: multipart/form-data

file: contacts.csv
```

```json
// 202 Accepted
{
  "job_id": "8f3c...",
  "status": "pending",
  "status_url": "/api/v1/imports/8f3c..."
}
```

**Implementation notes:**
- Stream parse (`csv` module), don’t load huge files into memory
- Validate headers + per-row; collect row errors into a report CSV
- Use batch `bulk_create` / upsert
- Idempotency key or job hash to avoid double import
- Auth + size limits + virus scan in enterprise setups
- Rate-limit upload endpoints

**Sync alternative (small files only):** parse in request, return summary — OK under ~few thousand rows.

---

### API documentation & testing tools?

| Purpose | Tools |
|---------|-------|
| **Docs / contract** | OpenAPI 3, Swagger UI, ReDoc, **drf-spectacular**, Stoplight |
| **Manual testing** | Postman, Insomnia, Bruno, HTTPie, curl |
| **Automated API tests** | pytest + DRF `APIClient`, Postman/Newman, REST Assured |
| **Contract testing** | Pact, Schemathesis |
| **Load testing** | k6, Locust, JMeter |
| **Mock from OpenAPI** | Prism, WireMock |

**Best practice:** OpenAPI is the source of truth; generate docs/SDKs from it.

---

### Tools for mocking APIs?

| Tool | Notes |
|------|-------|
| **Postman Mock Server** | From collections |
| **WireMock** | Java; powerful stubbing |
| **Mockoon** | Desktop local mocks |
| **MSW (Mock Service Worker)** | Frontend JS |
| **Prism** | Mock from OpenAPI |
| **json-server** | Quick fake REST from JSON |
| **django-rest-framework** browsable API / fixtures | Dev only |

Use mocks so frontend/mobile work before backend is ready, and for contract isolation in tests.

---

### API-level rate limiting? / Describe how you would implement rate limiting

**Goal:** protect capacity, stop abuse, enforce plan tiers.

**Algorithms:** fixed window, sliding window, token bucket, leaky bucket.

**Where:** API gateway (Kong, AWS API Gateway, Nginx), middleware, or app (DRF throttling).

**Identity key:** API key, user id, IP, or combination.

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700000000
```

**DRF:**
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
        "uploads": "10/hour",
    },
}
```

Use **shared Redis cache** so limits work across multiple workers.

---

### REST vs GraphQL use case?

| | **REST** | **GraphQL** |
|--|----------|-------------|
| Best for | Public APIs, CRUD resources, HTTP caching | Complex UIs needing flexible shapes |
| Over/under fetch | Common (fixed responses) | Client asks exact fields |
| Caching | Natural with `GET` / CDN | Harder (usually POST) |
| Tooling | Extremely mature | Strong, but different ops concerns |
| Abuse risk | Rate limit endpoints | Need query depth/cost limits |
| Versioning | Explicit versions common | Evolve schema carefully |

**Use REST when:** resource-oriented public API, simple clients, CDN caching matters.  
**Use GraphQL when:** many clients with different field needs (web vs mobile), rapid UI iteration, BFF pattern.  
**Use gRPC when:** internal service-to-service, high performance.

---

### Schema validation strategies?

1. **OpenAPI request/response schemas** — validate at gateway or with middleware
2. **DRF Serializers** — field types, `validate_<field>`, object-level `validate`
3. **Pydantic / marshmallow** (FastAPI/Flask)
4. **JSON Schema** validators
5. **DB constraints** as last line (NOT NULL, CHECK, FK, UNIQUE)
6. **Contract tests** ensure producers/consumers stay aligned

```python
class ContactSerializer(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField(min_length=10, max_length=2000)

    def validate_message(self, value):
        if "http://" in value.lower() and "spam" in value.lower():
            raise serializers.ValidationError("Suspicious content")
        return value
```

Validate **at the edge** (API layer) before business logic/DB.

---

### Explain HATEOAS and how it relates to RESTful services

**HATEOAS** = **Hypermedia As The Engine Of Application State** (Richardson Maturity Model **Level 3**).

Responses include **links** telling the client what it can do next — clients discover actions instead of hardcoding all URLs.

```json
{
  "id": 42,
  "status": "submitted",
  "message": "Need pricing help",
  "_links": {
    "self": { "href": "/api/v1/contacts/42" },
    "cancel": { "href": "/api/v1/contacts/42/cancel", "method": "POST" }
  }
}
```

**Relation to REST:** Fielding’s REST includes hypermedia constraint; many “REST” APIs are Level 2 (resources + HTTP verbs) without HATEOAS.

**Practice today:** Full HATEOAS is rare for CRUD APIs; teams often use **OpenAPI** for discoverability instead. HATEOAS shines for workflows/state machines.

---

## 2. Auth, CORS, HTTP & Throttling

### Different authentication methods in REST API

| Method | How | When |
|--------|-----|------|
| **API Key** | Header/query `X-API-Key` | Server-to-server, simple |
| **HTTP Basic** | `Authorization: Basic base64(user:pass)` | Legacy; HTTPS only |
| **Session / Cookie** | Server session + cookie | Browser same-site apps (+ CSRF) |
| **Token** (DRF) | `Authorization: Token <key>` | Simple mobile/server clients |
| **JWT (Bearer)** | `Authorization: Bearer <jwt>` | Stateless SPA/mobile |
| **OAuth 2.0 / OIDC** | Access + refresh tokens | Third-party / delegated access |
| **mTLS** | Client certificates | High-security service mesh |

**DRF common setup:**
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}
```

Auth answers **who**; **permissions** answer **what they may do**.

---

### CORS

**CORS (Cross-Origin Resource Sharing)** lets browsers allow JS on origin A to call API on origin B.

Without CORS headers, browser blocks cross-origin XHR/fetch.

```python
# django-cors-headers
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", ...]  # near top

CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True
# Never CORS_ALLOW_ALL_ORIGINS = True in production with credentials
```

Preflight: browser sends `OPTIONS` before “non-simple” requests.

---

### Different HTTP methods supported by REST

| Method | Purpose | Safe | Idempotent | Typical status |
|--------|---------|------|------------|----------------|
| **GET** | Read | Yes | Yes | 200 |
| **POST** | Create / action | No | No | 201 / 202 |
| **PUT** | Full replace | No | Yes | 200 / 201 |
| **PATCH** | Partial update | No | No* | 200 |
| **DELETE** | Remove | No | Yes | 204 / 200 |
| **HEAD** | Headers only | Yes | Yes | 200 |
| **OPTIONS** | Allowed methods / CORS | Yes | Yes | 200 |

\*PATCH idempotency depends on how you define the patch.

---

### Throttling

See rate limiting above. In DRF, throttling runs after authentication and before the view; exceeded limits → **429 Too Many Requests**.

Scoped example for expensive endpoints:
```python
class BulkUploadView(APIView):
    throttle_scope = "uploads"
```

---

## 3. API Observability

### What is API Observability? What are the 4 pillars?

**API Observability** = ability to understand production API behavior from telemetry — diagnose latency, errors, and user impact without guessing.

**Four pillars (MELT):**

| Pillar | What | Examples |
|--------|------|----------|
| **Metrics** | Numeric time series | RPS, p50/p95/p99 latency, error rate, saturation |
| **Events** | Discrete notable occurrences | Deploy, config change, incident, feature flag flip |
| **Logs** | Detailed records of what happened | Access logs, errors, audit trails (with request ids) |
| **Traces** | End-to-end request path | Trace across API → DB → cache → Celery |

**Practical extras:** correlation/request IDs in every log; OpenTelemetry; dashboards/alerts on SLOs (e.g. 99% of GETs < 300ms).

---

## 4. Django REST Framework (DRF)

### How do you create a simple API view in Django REST Framework?

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class HelloAPIView(APIView):
    def get(self, request):
        return Response({"message": "Hello"}, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get("name")
        if not name:
            return Response({"name": "This field is required."}, status=400)
        return Response({"message": f"Hello, {name}"}, status=201)
```

```python
# urls.py
path("hello/", HelloAPIView.as_view()),
```

---

### How do you serialize data in Django REST Framework?

Serializers convert complex types (model instances) ↔ JSON and validate input.

```python
from rest_framework import serializers
from .models import Contact

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "name", "email", "message", "created_at"]
        read_only_fields = ["id", "created_at"]

# Usage
ser = ContactSerializer(data=request.data)
ser.is_valid(raise_exception=True)
contact = ser.save()
return Response(ContactSerializer(contact).data, status=201)
```

`Serializer` for non-model payloads; `ModelSerializer` for models.

---

### How do you create a viewset in Django REST Framework?

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all().order_by("-created_at")
    serializer_class = ContactSerializer

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        obj = self.get_object()
        obj.is_archived = True
        obj.save(update_fields=["is_archived"])
        return Response({"status": "archived"})
```

```python
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contact")
urlpatterns = router.urls
# → list/create/retrieve/update/partial_update/destroy routes
```

---

### How do you handle file uploads in Django REST Framework?

1. Model: `FileField` / `ImageField`
2. Serializer includes the field
3. View parses multipart (`MultiPartParser`, `FormParser`)
4. Client sends `multipart/form-data`

```python
class Document(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="uploads/%Y/%m/")

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file"]

class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        ser = DocumentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=201)
```

```bash
curl -F "title=Resume" -F "file=@resume.pdf" https://api.example.com/documents/
```

Set `DATA_UPLOAD_MAX_MEMORY_SIZE`, validate content type/size, use cloud storage (`django-storages`) in production.

---

### What is the difference between APIView and ViewSet in DRF?

| | **APIView** | **ViewSet** |
|--|-------------|-------------|
| Structure | Explicit `get`/`post`/… methods | Actions: `list`, `retrieve`, `create`, … |
| Routing | Manual `path(..., AsView)` | `Router` generates URLs |
| Best for | Custom one-off endpoints | Standard CRUD resources |
| Boilerplate | More for CRUD | Less with `ModelViewSet` |
| Extra actions | Extra methods + urls | `@action` decorator |

`GenericAPIView` + mixins sit in between. `ViewSet` ≈ collection of actions bound by a router.

---

### How do you add authentication to an API view in DRF?

```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

class SecureContactList(APIView):
    authentication_classes = [JWTAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user is authenticated
        ...
```

Or globally in `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]` / `DEFAULT_PERMISSION_CLASSES`.

Per-action on viewsets:
```python
def get_permissions(self):
    if self.action == "create":
        return [AllowAny()]
    return [IsAdminUser()]
```

---

## 5. Coding: Contact Us API

### Requirement

Create a simple Django REST API for a **Contact Us** feature: users submit contact info + message; store in DB.

### Models

```python
# contacts/models.py
from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.subject or 'No subject'}"
```

### Serializer

```python
# contacts/serializers.py
from rest_framework import serializers
from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = [
            "id", "name", "email", "phone", "subject",
            "message", "created_at", "is_resolved",
        ]
        read_only_fields = ["id", "created_at", "is_resolved"]

    def validate_message(self, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters.")
        return value
```

### Views — option A: APIView (submit only)

```python
# contacts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle

from .serializers import ContactMessageSerializer

class ContactUsCreateAPIView(APIView):
    """Public endpoint: anyone can submit a contact form."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "detail": "Thank you! We received your message.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
```

### Views — option B: ViewSet (create public, list/admin restricted)

```python
from rest_framework import viewsets, permissions

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "detail": "Thank you! We received your message.",
                "data": response.data,
            },
            status=status.HTTP_201_CREATED,
        )
```

### URLs

```python
# contacts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactUsCreateAPIView, ContactMessageViewSet

router = DefaultRouter()
router.register(r"contacts", ContactMessageViewSet, basename="contact")

urlpatterns = [
    path("contact-us/", ContactUsCreateAPIView.as_view(), name="contact-us"),
    path("", include(router.urls)),
]
```

```python
# project/urls.py
urlpatterns = [
    path("api/v1/", include("contacts.urls")),
]
```

### Settings snippets

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "contacts",
]

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/hour",  # limit contact spam
    },
}
```

### Example request / response

```bash
curl -X POST http://127.0.0.1:8000/api/v1/contact-us/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ravi Kumar",
    "email": "ravi@example.com",
    "phone": "9876543210",
    "subject": "Partnership",
    "message": "Hi, I would like to discuss a partnership opportunity."
  }'
```

```json
{
  "detail": "Thank you! We received your message.",
  "data": {
    "id": 1,
    "name": "Ravi Kumar",
    "email": "ravi@example.com",
    "phone": "9876543210",
    "subject": "Partnership",
    "message": "Hi, I would like to discuss a partnership opportunity.",
    "created_at": "2026-07-27T15:00:00.000000Z",
    "is_resolved": false
  }
}
```

### Interview talking points for this feature

- Public `POST`, admin-only list/retrieve
- Validation via serializer (email format, min message length)
- Throttling against spam
- Optional: Celery email notification to support team on create
- Optional: `Idempotency-Key` if UI may double-submit
- Don’t expose `is_resolved` as writable for anonymous users

---

## Quick Cheat Sheet

| Topic | One-liner |
|-------|-----------|
| Idempotency | Same request → same effect; use keys for POST |
| Safe methods | GET/HEAD/OPTIONS — no state change |
| Versioning | Prefer `/api/v1/` for public APIs |
| Breaking change | New version + deprecation window |
| HATEOAS | Hypermedia links drive next actions |
| CORS | Browser cross-origin permission headers |
| Throttle | Rate limit → 429 |
| Observability | Metrics, Events, Logs, Traces |
| APIView vs ViewSet | Manual verbs vs router CRUD actions |
| Contact Us | `AllowAny` create + serializer + throttle |

---

*Sources: HTTP semantics (RFC 9110), common public API practices (Stripe-style idempotency, OpenAPI), DRF documentation patterns.*


## 1. Resource Modeling & URI Architecture

### Q1: Explain the Richardson Maturity Model and its relevance to enterprise API design.

**Answer:** The Richardson Maturity Model breaks down the path toward true REST into four distinct levels:

* **Level 0 (The Swamp of POX):** Uses HTTP strictly as a transport mechanism for remote procedure calls (RPC). Usually hits a single endpoint (e.g., `/api/endpoint`) using one method (typically `POST`) with the action defined entirely in the payload.
* **Level 1 (Resources):** Introduces individual URIs for distinct resources (e.g., `/orders`, `/orders/123`), but still communicates using a single HTTP method or generic status codes.
* **Level 2 (HTTP Verbs):** Utilizes standard HTTP methods properly (`GET` for safe reads, `POST` for creation, `DELETE` for removal) and leverages native HTTP status codes (200, 201, 404, 409) for communication.
* **Level 3 (Hypermedia Controls):** Implements HATEOAS (Hypermedia As The Engine Of Application State). Responses include links that explicitly inform the client of the next valid actions they can take from the current resource state.

### Q2: Is HATEOAS practical for high-throughput backend microservices? What are the trade-offs?

**Answer:** In highly coupled or rapidly scaling internal microservices, formal HATEOAS is rarely deployed due to its trade-offs.

* **Pros:** Complete decoupling of client routing logic; the server dictates the business workflow state dynamically.
* **Cons:** Introduces significant network payload overhead by packing links into every JSON wrapper, increases serialization/deserialization CPU costs, and forces upstream clients to continually parse structures to discover endpoints rather than relying on standard code-generated client libraries (e.g., OpenAPI stubs).

### Q3: How do you choose between sub-resources (`/users/123/orders`) and query parameters (`/orders?user_id=123`)?

**Answer:** Use sub-resources when the child resource's lifecycle is tightly bound to and strictly dependent on the parent resource (e.g., an order line item cannot exist without an order: `/orders/123/items/4`). Use query parameters when you are querying a primary, independent resource collection where the relationship acts as a filter criterion (e.g., orders can be queried independently of a user, or filtered by status, date, or department).

### Q4: How should non-RESTful actions (e.g., `/jobs/45/cancel` or `/accounts/12/freeze`) be modeled gracefully?

**Answer:** True REST treats everything as a noun (resource). When modeling state-machine mutations or specific actions, you have three primary architectural options:

1. **Treat the action as a sub-resource/command pattern:** Treat the execution path as an independent collection. `POST /jobs/45/cancellations` creates a new cancellation record.
2. **Treat it as a partial patch update:** Keep the noun dominant and execute a state modification payload. `PATCH /accounts/12` with a body of `{"status": "frozen"}`.
3. **Expose an action parameter (Controller pattern):** If the mutation involves complex, multi-entity business logic that doesn't fit a simple field edit, append a clear semantic verb after the resource identifier, utilizing `POST` to execute the transaction: `POST /accounts/12/freeze`.

### Q5: Should resource collections use flat or highly nested URIs? Explain the constraint.

**Answer:** Prefer flat URIs over deeply nested structural paths. Avoid nesting deeper than one level (e.g., stop at `/parents/123/children`). Deeply nested paths like `/companies/1/departments/5/teams/12/members/99` make endpoints rigid, create unnecessary dependencies on parent resource lookups, complicate routing definitions, and result in bloated, unreadable code contracts. Instead, expose `/members/99` directly, routing contextual parent scopes via optional query filters.

---

## 2. HTTP Methods, Contracts & Idempotency

### Q6: What is the technical difference between `PUT` and `PATCH` regarding payload processing?

**Answer:** `PUT` is structurally defined as a complete resource replacement. The client sends a payload representing the absolute state of the object; missing fields are implicitly cleared or reset to defaults. `PATCH` executes a partial modification of an existing resource. The payload contains only the fields intended for modification, leaving unspecified parameters intact.

### Q7: Compare JSON Merge Patch and JSON Patch (RFC 6902). When do you use each?

**Answer:**

* **JSON Merge Patch (RFC 7396):** The payload is a simple JSON object mimicking the target resource. Passing `{"title": null}` nullifies a field, while omitting a key leaves it untouched. It is easy to parse but cannot easily manipulate individual array indices.
* **JSON Patch (RFC 6902):** The payload is an explicit array of mutation instruction objects specifying operations. For example: `[{"op": "add", "path": "/tags/0", "value": "featured"}]`. This structure supports atomic, precise adjustments to deep nested keys and arrays.

### Q8: How do you guarantee idempotency on non-idempotent endpoints like a `POST` payment capture?

**Answer:** You enforce an application-level idempotency contract using unique tokens:

* The client generates a unique `Idempotency-Key` (e.g., UUIDv4) and transmits it inside the request header.
* The backend worker intercepts the request and verifies the key's presence in a central distributed cache (like Redis) using an atomic operation.
* If the key exists, the backend instantly returns the cached response from the original execution. If it is a new request, the backend locks the key, processes the execution path, saves the final output contract to the cache with a defined time-to-live (TTL), and returns the payload.

### Q9: If a client generates a UUID upfront to create a resource, should you expose a `POST` or `PUT` endpoint?

**Answer:** If the client dictates the exact URI path where the resource will reside (because it already owns the unique identifier), you should expose a `PUT` endpoint targeting that specific coordinate (`PUT /users/f81d4fae-7dec-11d0-a765-00a0c91e6bf6`). If the server remains responsible for generating the final ID and allocating the resource's destination, expose a generic collection `POST` endpoint instead (`POST /users`).

### Q10: Classify standard HTTP methods into Safe and Idempotent groups.

**Answer:**

| HTTP Method | Safe? (Does not mutate state) | Idempotent? (Repeated executions yield same state) |
| --- | --- | --- |
| **GET** | Yes | Yes |
| **HEAD** | Yes | Yes |
| **OPTIONS** | Yes | Yes |
| **POST** | No | No |
| **PUT** | No | Yes |
| **PATCH** | No | No (Can be idempotent if written carefully) |
| **DELETE** | No | Yes |

*Note: A `PATCH` operation like `{"op": "increment", "path": "/views"}` changes the server state with every consecutive call, making it non-idempotent.*

### Q11: When is it architecturally appropriate to return a `202 Accepted` status code instead of `200 OK` or `201 Created`?

**Answer:** Return a `202 Accepted` status code for asynchronous, long-running operations where processing is accepted but not yet finalized (e.g., processing a massive report export or triggering an async machine learning workflow). The response payload should include a tracking resource handle or header (`Location: /tasks/xyz`) allowing the client to poll for the final execution status.

---

## 3. Query Optimization: Pagination, Filtering & Versioning

### Q12: Compare Offset-based and Cursor-based pagination. When does offset break down?

**Answer:**

* **Offset-based (`?limit=20&offset=100`):** Relies on SQL `LIMIT` and `OFFSET`. It breaks down on large datasets because database engines must scan and discard all rows leading up to the offset value ($O(N)$ read costs). It also suffers from element skipping/duplication if rows are appended or deleted mid-scroll.
* **Cursor-based (`?limit=20&starting_after=eyJVdWlkIjp9`):** Uses an encoded pointer indicating the last seen row property (usually an ID or timestamp combination). The query searches directly using indexed conditional boundaries (`WHERE id > last_seen_id ORDER BY id LIMIT 20`), ensuring constant $O(1)$ database execution performance regardless of depth.

### Q13: Design an intuitive, readable query parameter structure for an API requiring multi-field sorting capabilities.

**Answer:** A clean convention is to accept a single comma-delimited list parameter called `sort`. The direction is specified by appending a leading modifier prefix, where a standard string implies ascending order and a negative sign (`-`) enforces descending order.

```http
GET /products?sort=-created_at,price,name

```

This avoids nested JSON payloads in URL structures and allows the backend to easily split strings into structural query sorting tokens.

### Q14: How do you construct a standardized query filtering layout for complex operators (e.g., Greater Than, In Array)?

**Answer:** For complex logic patterns, utilize square bracket indexing notation keys or parameter object mappings to attach operational constraints:

* **Brackets approach:** `GET /cars?price[gte]=20000&status[in]=available,reserved`
* **LHS Brackets parsing:** The backend extracts the parameter array tokens, mapping `price -> gte -> 20000` straight into your ORM or SQL condition builder pipelines.

### Q15: Evaluate the three primary API versioning strategies: URI, Custom Headers, and Accept Headers.

**Answer:**

* **URI Versioning (`/v1/users`):** Highly readable and easily cached by standard CDN layers. However, it treats the same conceptual asset as a completely different resource path across versions.
* **Custom Headers (`X-API-Version: 2.0`):** Maintains clean resource URIs. The downside is it requires clients to control header mutations and complicates standard browser-based link testing.
* **Accept Header/Media Type (`Accept: application/vnd.company.v2+json`):** The most theoretically pure REST approach (content negotiation). It allows the same resource coordinate to yield different output representations. The trade-off is complex routing overhead at the API gateway layer and steep parsing friction for downstream clients.

### Q16: How can you mitigate over-fetching and under-fetching in a pure REST environment without adopting GraphQL?

**Answer:** Implement the **Sparse Fieldsets** design pattern. Allow clients to pass a native parameter (such as `fields`) containing a comma-separated list of the exact attributes they want returned in the final payload:

```http
GET /users/123?fields=id,email,display_name

```

The backend intercepts this configuration parameter dynamically, altering the primary data query or filtering the final serialization mapper to exclude heavy attributes (like large bio text blocks or embedded relationships).

---

## 4. API Security, Contracts & Resiliency

### Q17: What is Broken Object Level Authorization (BOLA) in REST APIs, and how do you design against it?

**Answer:** BOLA (historically known as IDOR) occurs when an endpoint accepts a resource identifier (`GET /accounts/999`) but fails to validate whether the authenticated user has authorization to access that specific record. To prevent BOLA, you should avoid relying solely on authentication checks. Every query must trace ownership constraints directly, evaluating whether the session token's user identity links cleanly to the requested entity record:

```sql
SELECT * FROM accounts WHERE id = :account_id AND user_id = :current_user_id;

```

### Q18: Why are sequential integer IDs (Auto-increments) dangerous to expose in public REST endpoints? What are the alternatives?

**Answer:** Sequential IDs expose your system to enumeration attacks, allowing malicious actors to crawl resources systematically by guessing adjacent values (`/invoices/1001`, `/invoices/1002`). They also leak business telemetry data, revealing your exact total volume of sales or users to competitors. Prevent this by using non-enumerable alternatives like **UUIDv4** or **NanoID** for all external-facing resource handles.

### Q19: Design an industrial-standard rate-limiting communication protocol via HTTP response headers.

**Answer:** When an API enforces traffic limits, it should convey usage constraints transparently via standard headers on every request:

* `X-RateLimit-Limit`: The maximum allowance allowed in the current time frame window.
* `X-RateLimit-Remaining`: The volume of requests remaining before exhaustion hits.
* `X-RateLimit-Reset`: The Unix timestamp indicating exactly when the active limit quota resets.
* If a client breaches constraints, return a `429 Too Many Requests` status code combined with a `Retry-After` header indicating the required wait duration in seconds.

### Q20: How do you design client contract definitions for missing or invalid resource scenarios?

**Answer:** Consistency across exceptional paths is critical for a predictable API contract:

* For data validation failures, return a `422 Unprocessable Entity` or `400 Bad Request` status code accompanied by a structured JSON payload detailing exactly which fields failed validation and why (e.g., using a layout inspired by RFC 7807 Problem Details).
* For resources that do not exist, return a `404 Not Found` status code. Ensure the response format matches your standard layout, using a consistent schema type (such as `{"type": "error", "message": "Resource not found"}`) so client SDK engines parse error formats uniformly.

### Q21: What structural practices shield public multi-part file upload endpoints from resource exhaustion attacks?

**Answer:** At the API design layer, enforce explicit constraints: restrict maximum allowable file sizes via gateway configurations, whitelist allowed MIME types, and read input payloads as byte streams rather than loading whole files into system memory buffers. In addition, offload long-running virus scanning operations to background worker queues, returning a `202 Accepted` status code immediately to keep web worker threads open.

---

## 5. Caching, Lifecycle Optimization & Advanced Operations

### Q22: Explain the mechanics of conditional GET requests using ETags and `If-None-Match`.

**Answer:** An `ETag` (Entity Tag) is a unique cryptographic hash or version string representing the state of a resource at a specific point in time.

* When a client first requests a resource, the server includes the hash header: `ETag: "w/34a11b"`.
* For subsequent requests, the client passes this string back inside the `If-None-Match: "w/34a11b"` header.
* The server calculates the resource's current hash. If it matches the client's token, the server bypasses content serialization and returns a lightweight `304 Not Modified` status code without a payload body, saving network bandwidth.

### Q23: How do `Cache-Control` directives like `public`, `private`, `no-cache`, and `no-store` guide proxy networks?

**Answer:**

* `public`: Indicates the response can be cached by any intermediate node, including public shared reverse proxies and CDNs.
* `private`: Restricts caching exclusively to the end-client browser device; intermediate public gateways must not store it.
* `no-cache`: Forces the client to revalidate the asset with the origin server via ETags before using the cached copy.
* `no-store`: Explicitly commands all layers to completely avoid caching or recording the response payload bytes under any circumstance.

### Q24: Detail the asynchronous request-reply design pattern for handling long-running operations.

**Answer:**

1. The client triggers an operation via `POST /reports/generate`.
2. The server accepts the transaction, registers a background task handle, and immediately returns a `202 Accepted` status code. It includes a tracking URL via the `Location: /tasks/98a` header.
3. The client hits `GET /tasks/98a` to poll the status. The server returns a status field (`pending`, `processing`, or `completed`).
4. Once processing finishes, the task endpoint updates its payload state to point to the final target location: `{"status": "completed", "result_url": "/reports/file-abc.pdf"}`.

### Q25: How do you model atomic transaction patterns involving multiple separate resources in a RESTful way?

**Answer:** If mutations across multiple entities must execute atomically, avoid making separate HTTP calls that risk partial failures. Instead, encapsulate the process into an intentional business transaction resource. For example, use a checkout endpoint (`POST /checkouts`) that accepts a composite payload containing order data, payment details, and shipping metadata, ensuring the entire block executes within a single database transaction boundary.

### Q26: Design a batch processing endpoint pattern that handles bulk mutations efficiently.

**Answer:** For high-volume bulk mutations, expose a dedicated bulk execution coordinator endpoint (`POST /products/batch`). The payload accepts an array of mutation instructions. The response contract should return a `200 OK` code containing an array of operational outcomes matching the input positions, with each index detailing its individual execution status:

```json
{
  "results": [
    {"status": 201, "id": "101"},
    {"status": 422, "errors": ["Invalid price format"]}
  ]
}

```

### Q27: What safety protocols must be designed into a webhooks notification delivery service?

**Answer:** A resilient webhooks architecture requires several key design patterns:

* **Cryptographic Signatures:** Include an `X-Hub-Signature-256` header containing an HMAC hash of the payload body calculated using a shared secret key, allowing clients to verify the request's origin.
* **Idempotency Tracking:** Include a unique event identifier (`X-Event-Id`) in the header so clients can filter out duplicate webhook deliveries.
* **Retry Strategy:** Implement an exponential backoff retry pipeline to handle client timeouts gracefully without overwhelming their servers.

### Q28: How do you ensure a `PATCH` update incrementing an entity counter remains idempotent?

**Answer:** A raw arithmetic statement like `PATCH` with `{"views": "+1"}` is inherently non-idempotent. To make this safe, you can use conditional mutations via an ETag or version lock check (`If-Match: "version_4"`). The database transaction verifies the version string matches before committing the increment; if a duplicate request hits the server out of order, the version check fails, preventing duplicate counting.

### Q29: Can you isolate Command Query Responsibility Segregation (CQRS) patterns cleanly at the API design layer?

**Answer:** Yes. You structure your endpoint routing paths to clearly separate data mutation channels from query channels. Read paths (`GET`) map to highly cached, denormalized read-replica databases, optimized for rapid retrieval and filtering. Write paths (`POST`, `PUT`, `DELETE`) route through separate middleware handling transaction validations, domain events, and main database execution chains.

### Q30: How do you design an API to handle resource deprecation gracefully without breaking legacy client integrations?

**Answer:** Implement a structured deprecation lifecycle using standardized HTTP response headers. When an endpoint is marked for removal, include a `Deprecation` header specifying the date or status of the deprecation, along with a `Sunset` header indicating the exact timestamp when the endpoint will be turned off. This communicates timeline constraints directly to clients before the route is removed.

