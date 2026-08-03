# FastAPI Interview Questions & Answers

> Interview prep covering FastAPI core, security, testing, WebSockets, middleware, async pitfalls, RabbitMQ integration, and coding scenarios.

---

## Table of Contents

1. [General FastAPI Knowledge](#1-general-fastapi-knowledge)
2. [Request and Response Handling](#2-request-and-response-handling)
3. [Security](#3-security)
4. [Testing](#4-testing)
5. [Deployment and Performance](#5-deployment-and-performance)
6. [WebSocket Support](#6-websocket-support)
7. [Middleware](#7-middleware)
8. [Extras](#8-extras)
9. [Scenario-Based Questions](#9-scenario-based-questions)
10. [Async FastAPI + Sync / RabbitMQ](#10-async-fastapi--sync--rabbitmq)
11. [Coding Problems](#11-coding-problems)

---

## 1. General FastAPI Knowledge

### What is FastAPI, and how does it differ from other web frameworks in Python?

**FastAPI** is a modern, high-performance Python web framework for building APIs, built on **Starlette** (ASGI) and **Pydantic** (validation).

| Aspect | FastAPI | Flask | Django |
|--------|---------|-------|--------|
| Style | ASGI, async-first | WSGI, sync | Full batteries, MVT |
| Validation | Automatic via type hints + Pydantic | Manual / extensions | Forms / serializers (DRF) |
| Docs | Auto OpenAPI / Swagger / ReDoc | Add-ons | Spectacular / CoreAPI for DRF |
| Performance | Very high (uvicorn + async) | Good for sync | Good; heavier |
| DI | Built-in `Depends` | Limited | Settings / services DIY |
| Best for | APIs / microservices | Simple apps / APIs | Full products + admin |

**Key differentiators:** native async, type-hint validation, automatic interactive docs, dependency injection, excellent developer UX.

---

### Explain automatic data validation in FastAPI. How does it leverage Python type hints?

FastAPI reads **function parameter type annotations** and builds **Pydantic models** / validators. Invalid data → **422 Unprocessable Entity** with detailed errors — before your business logic runs.

```python
from fastapi import FastAPI, Query, Path
from pydantic import BaseModel, EmailStr, Field

app = FastAPI()

class UserCreate(BaseModel):
    email: EmailStr
    age: int = Field(ge=18, le=120)
    name: str = Field(min_length=2, max_length=100)

@app.post("/users")
def create_user(user: UserCreate):
    return user  # already validated
```

- Path/query/body inferred from types and defaults
- Nested models, enums, custom validators (`field_validator`)
- Response models also validated/filtered via `response_model=`

---

### How does FastAPI handle asynchronous programming, and what benefits does it provide?

- Endpoints can be `async def` (run on event loop) or `def` (run in threadpool)
- Native `await` for I/O: DB (asyncpg), HTTP (httpx), queues (aio-pika)
- ASGI server (Uvicorn/Hypercorn) multiplexes many connections on few threads

**Benefits:** high concurrency for I/O-bound workloads, lower resource use vs one-thread-per-request, natural fit for WebSockets and long-lived connections.

**Critical rule:** never call **blocking** I/O inside `async def` without offloading — that freezes the whole event loop.

---

### What is dependency injection in FastAPI? Example?

**DI** = declare reusable dependencies; FastAPI resolves and injects them into path operations via `Depends()`.

```python
from fastapi import Depends, HTTPException, Header

async def get_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid auth header")
    return authorization.removeprefix("Bearer ").strip()

async def get_current_user(token: str = Depends(get_token)):
    user = await users_repo.by_token(token)
    if not user:
        raise HTTPException(401, "Unauthorized")
    return user

@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user
```

**Uses:** DB sessions, auth, pagination params, settings, shared clients. Supports sub-dependencies, caching per-request (`use_cache=True` default), and `yield` for cleanup (DB session close).

---

## 2. Request and Response Handling

### Explain the request and response lifecycle in a FastAPI application

1. Client → ASGI server (Uvicorn)
2. Middleware stack (inbound)
3. Routing matches path + method
4. Dependency injection resolved
5. Request parsing + **validation** (path/query/body)
6. Path operation function runs (`def`/`async def`)
7. Response data → optional `response_model` filter/serialize
8. Middleware stack (outbound)
9. ASGI sends HTTP response
10. Optional `BackgroundTasks` run after response is sent

Errors: `HTTPException`, validation → 422, unhandled → 500 (exception handlers).

---

### How does FastAPI handle query parameters and path parameters? Examples

```python
@app.get("/items/{item_id}")
async def read_item(
    item_id: int,                          # path param
    q: str | None = None,                  # optional query
    limit: int = Query(10, ge=1, le=100),  # query with constraints
):
    return {"item_id": item_id, "q": q, "limit": limit}

# GET /items/42?q=phone&limit=20
```

- Path params: required parts of URL path
- Query params: function params that are not path params and not body models
- `Annotated` style (modern): `q: Annotated[str | None, Query(max_length=50)] = None`

---

### What is the role of JSONResponse? Customize responses

`JSONResponse` (Starlette) builds an HTTP response with JSON body, status, headers, media type.

```python
from fastapi.responses import JSONResponse

@app.post("/orders")
async def create_order():
    return JSONResponse(
        status_code=201,
        content={"id": 1, "status": "created"},
        headers={"X-Request-ID": "abc-123"},
    )
```

Other responses: `ORJSONResponse`, `Response`, `StreamingResponse`, `FileResponse`, `RedirectResponse`, `HTMLResponse`.

You can also return dicts/Pydantic models — FastAPI wraps them; use `JSONResponse` when you need full control of status/headers/body encoding.

---

## 3. Security

### Security features — authentication and authorization

FastAPI provides utilities in `fastapi.security`:

| Tool | Use |
|------|-----|
| `HTTPBasic` | Basic auth |
| `HTTPBearer` / `HTTPAuthorizationCredentials` | Bearer tokens |
| `APIKeyHeader` / `APIKeyQuery` | API keys |
| `OAuth2PasswordBearer` | OAuth2 password flow + JWT apps |
| `OAuth2AuthorizationCodeBearer` | Auth code flow |

**AuthN** (who): extract & verify credentials in a dependency.  
**AuthZ** (what): check roles/permissions in dependencies or inside the route → `HTTPException(403)`.

Also: HTTPS termination, CORS config, trusted hosts middleware, input validation (injection resistance), password hashing (passlib/bcrypt) outside framework.

---

### Explain OAuth2 in FastAPI for securing APIs

Common pattern: **OAuth2 password flow** for login + **JWT access tokens**.

```python
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET, ALGO = "change-me", "HS256"

def create_access_token(sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    return jwt.encode({"sub": sub, "exp": expire}, SECRET, algorithm=ALGO)

@app.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(form.username, form.password)
    if not user:
        raise HTTPException(401, "Incorrect credentials")
    return {"access_token": create_access_token(user.username), "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return payload["sub"]
    except Exception:
        raise HTTPException(401, "Invalid token")

@app.get("/secure")
async def secure(user: str = Depends(get_current_user)):
    return {"user": user}
```

Swagger UI gets a built-in Authorize button via `OAuth2PasswordBearer`.

---

## 4. Testing

### How to write unit tests? Tools/libraries?

- **pytest** (standard)
- **httpx** + Starlette/FastAPI **`TestClient`** (sync) or **`AsyncClient`** (async)
- **pytest-asyncio** for async tests
- Factories/fixtures for DB (e.g. SQLAlchemy test session + rollback)
- Freezegun, respx/httpx mock for external HTTP

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user():
    r = client.post("/users", json={"email": "a@b.com", "age": 20, "name": "Ada"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"
```

---

### Role of TestClient

`TestClient` talks to your ASGI app **in-process** without a real server — great for endpoint tests.

```python
client = TestClient(app)
response = client.get("/items/1")
assert response.status_code == 200
```

- Supports cookies, headers, files, raises_server_exceptions
- Runs lifespan/startup events
- Background tasks typically complete before assertions return

For fully async tests: `async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:`

---

## 5. Deployment and Performance

### Deployment options — compare

| Option | Pros | Cons |
|--------|------|------|
| **Uvicorn** (+ Gunicorn workers) | Simple, production-proven | Manage process yourself |
| **Gunicorn `-k uvicorn.workers.UvicornWorker`** | Multi-worker, graceful reload | Still need reverse proxy |
| **Docker + K8s** | Scale, health checks | Ops complexity |
| **Serverless** (Mangum/AWS Lambda, Cloud Run) | Autoscale, low idle cost | Cold starts; WS limits |
| **PaaS** (Render, Railway, Fly.io) | Fast ship | Less control |

Typical prod: `Nginx/ALB → Gunicorn(UvicornWorker) × N → FastAPI` behind HTTPS.

---

### How does FastAPI achieve high performance?

1. **ASGI + async I/O** — high concurrency
2. **Starlette** — lean routing/middleware
3. **Pydantic v2** — fast Rust-backed validation
4. **Uvicorn** — uvloop/httptools optional speedups
5. Less framework overhead than full-stack frameworks for pure APIs

Still: performance depends on **not blocking the event loop**, efficient DB queries, and proper worker counts.

---

## 6. WebSocket Support

### What is WebSocket, and how does FastAPI support it?

**WebSocket** = full-duplex persistent TCP-based connection over HTTP upgrade — ideal for chat, live feeds, collaborative editors.

FastAPI/Starlette: `@app.websocket("/ws")` + `WebSocket` object.

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{room}")
async def ws_endpoint(websocket: WebSocket, room: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"room={room} echo: {data}")
    except WebSocketDisconnect:
        print("client left")
```

---

### WebSocket events in FastAPI

Typical app-level events (your protocol):
- `connect` / `disconnect`
- `message` / `broadcast`
- `join_room` / `leave_room`
- `ping` / `pong` (heartbeat)
- domain events: `draw_stroke`, `cursor_move`, `chat_message`

Implement as JSON envelopes:

```json
{"type": "draw_stroke", "payload": {"x": 10, "y": 20, "color": "#000"}}
```

Manage connections with a connection-manager class (accept, disconnect, broadcast).

---

## 7. Middleware

### What is middleware, and how to use it in FastAPI?

Middleware wraps every request/response — cross-cutting concerns.

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.perf_counter() - start)
    return response
```

Or `app.add_middleware(CORSMiddleware, ...)`.

**Useful for:** CORS, logging, auth gate, timing, request IDs, GZip, trusted hosts, rate limiting.

---

## 8. Extras

### Integrating FastAPI with a database (example)

SQLAlchemy 2.0 async + PostgreSQL:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from fastapi import Depends

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    return user
```

Alternatives: Tortoise ORM, SQLModel, databases + encode/databases, Prisma.

---

### How does FastAPI handle CORS?

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Avoid `allow_origins=["*"]` with credentials in production.

---

### Role of BackgroundTasks

Run work **after** sending the response (same process) — emails, light cleanup, cache warm.

```python
from fastapi import BackgroundTasks

def write_log(msg: str):
    with open("log.txt", "a") as f:
        f.write(msg + "\n")

@app.post("/send")
async def send(background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, "notification queued")
    return {"status": "ok"}
```

**Not for heavy/long jobs** — use Celery / RQ / RabbitMQ workers. Tasks die if process crashes after response.

---

### Role of Depends

`Depends(callable)` declares a dependency FastAPI will call and inject.

```python
def common_params(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/items")
def list_items(commons: dict = Depends(common_params)):
    return commons
```

With `yield`: setup/teardown (DB session). Nested `Depends` form a graph resolved per request.

---


## 9. Scenario-Based Questions

### Scenario 1: Request Validation (user registration)

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=18)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v) or not re.search(r"\d", v):
            raise ValueError("Password needs an uppercase letter and a digit")
        return v

@app.post("/register", status_code=201)
async def register(payload: RegisterIn):
    # hash password, save user...
    return {"email": payload.email, "full_name": payload.full_name}
```

Invalid body → automatic **422** with field errors.

---

### Scenario 2: Dependency Injection for authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

async def require_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    user = await auth_service.verify(creds.credentials)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return user

@app.get("/secure-data")
async def secure_data(user=Depends(require_user)):
    return {"message": "secret", "user_id": user.id}
```

---

### Scenario 3: Asynchronous WebSocket messaging

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from collections import defaultdict

app = FastAPI()

class Hub:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, room: str, ws: WebSocket):
        await ws.accept()
        self.rooms[room].add(ws)

    def disconnect(self, room: str, ws: WebSocket):
        self.rooms[room].discard(ws)

    async def broadcast(self, room: str, message: str):
        dead = []
        for ws in self.rooms[room]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(room, ws)

hub = Hub()

@app.websocket("/ws/chat/{room}")
async def chat(room: str, websocket: WebSocket):
    await hub.connect(room, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            await hub.broadcast(room, text)
    except WebSocketDisconnect:
        hub.disconnect(room, websocket)
```

---

### Scenario 4: Testing example

```python
# test_register.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_ok():
    r = client.post("/register", json={
        "email": "ada@example.com",
        "password": "Secret1!",
        "full_name": "Ada Lovelace",
        "age": 36,
    })
    assert r.status_code == 201
    assert r.json()["email"] == "ada@example.com"

def test_register_weak_password():
    r = client.post("/register", json={
        "email": "ada@example.com",
        "password": "weak",
        "full_name": "Ada",
        "age": 36,
    })
    assert r.status_code == 422
```

---

### Scenario 5: PostgreSQL CRUD with SQLAlchemy async

```python
# models + session as in Extras section

from sqlalchemy import select

@app.post("/users", status_code=201)
async def create_user(email: str, db: AsyncSession = Depends(get_db)):
    user = User(email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

@app.put("/users/{user_id}")
async def update_user(user_id: int, email: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404)
    user.email = email
    await db.commit()
    return user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404)
    await db.delete(user)
    await db.commit()
```

---

### Scenario 6: Logging middleware

```python
import logging
from datetime import datetime, timezone
from fastapi import Request

logger = logging.getLogger("api")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    ts = datetime.now(timezone.utc).isoformat()
    logger.info("req method=%s path=%s ts=%s", request.method, request.url.path, ts)
    response = await call_next(request)
    logger.info("res status=%s path=%s", response.status_code, request.url.path)
    return response
```

---

### Scenario 7: Collaborative drawing WebSocket events

| Event | Direction | Payload ideas |
|-------|-----------|---------------|
| `join` | C→S | `{room_id, user_id}` |
| `presence` | S→C | `{users: [...]}` |
| `stroke_start` | C→S | `{id, color, width}` |
| `stroke_point` | C→S | `{id, x, y}` |
| `stroke_end` | C→S | `{id}` |
| `stroke_broadcast` | S→C | relay stroke to peers |
| `clear_canvas` | C↔S | `{by}` |
| `undo` | C↔S | `{stroke_id}` |
| `cursor_move` | C→S→C | `{user_id, x, y}` |
| `sync_state` | S→C | full scene for late joiners |
| `heartbeat` | both | keep-alive |

Server validates, optionally persists strokes, broadcasts to room except sender.

---

### Scenario 8: BackgroundTasks for PDF report

```python
from fastapi import BackgroundTasks
from uuid import uuid4

jobs: dict[str, str] = {}

def generate_pdf(job_id: str, user_email: str):
    # heavy work...
    path = f"/tmp/{job_id}.pdf"
    # create PDF at path
    jobs[job_id] = "ready"
    send_email(user_email, f"Report ready: /reports/{job_id}")

@app.post("/reports")
async def request_report(email: str, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    jobs[job_id] = "processing"
    background_tasks.add_task(generate_pdf, job_id, email)
    return {"job_id": job_id, "status": "processing"}

@app.get("/reports/{job_id}")
async def report_status(job_id: str):
    return {"job_id": job_id, "status": jobs.get(job_id, "unknown")}
```

For production: use a real job queue (Celery/RabbitMQ), store status in Redis/DB, email/webhook on completion — `BackgroundTasks` is only for light post-response work.

---

### Scenario 9: Deployment (choose Gunicorn + Uvicorn workers + Docker)

**Steps:**
1. `Dockerfile` with app + `gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 main:app`
2. Env vars for secrets/DB URL
3. Health endpoint `/health`
4. Reverse proxy (Nginx/ALB) TLS termination
5. Migrate DB on release
6. Rolling deploy / K8s Deployment + Service + HPA
7. Logs/metrics (OTel, Prometheus)
8. `LIMIT` workers ≈ `(2 × CPU) + 1` as starting point; tune with load tests

**Other options:** Cloud Run, AWS ECS/Fargate, Railway — same ASGI entrypoint.

---

### Scenario 10: CORS for separate frontend domain

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
```

Frontend at different origin can then call the API; preflight `OPTIONS` handled by middleware.

---


## 10. Async FastAPI + Sync / RabbitMQ

> Team note: mixing `def` and `async def` needs care with RabbitMQ locking and structlog context. External/internal HTTP must be **non-blocking async** so one slow call doesn’t stall the async queue.

### Explain challenges of calling sync functions from async FastAPI routes

If you `async def` a route and call blocking code (`requests.get`, `psycopg2`, `time.sleep`, sync Pika):

- Event loop stalls → **all** requests/WebSockets freeze
- Latency spikes and timeouts cascade

**Mitigations:**
1. Use async libraries (`httpx`, `asyncpg`, `aio-pika`)
2. Offload sync with `await asyncio.to_thread(fn, ...)` or `run_in_executor`
3. Or declare route as plain `def` so FastAPI runs it in threadpool
4. Push heavy work to workers (RabbitMQ/Celery)

---

### `asyncio.to_thread()` vs `run_in_executor()`

| | `asyncio.to_thread(fn, *args)` | `loop.run_in_executor(executor, fn, *args)` |
|--|-------------------------------|---------------------------------------------|
| API | Simpler (3.9+) | More control |
| Pool | Default thread pool | Pass custom `ThreadPoolExecutor` / `ProcessPoolExecutor` |
| Use | Quick offload of blocking I/O | Tune pool size; CPU-bound → **process** pool |

```python
result = await asyncio.to_thread(sync_db_call, user_id)
result = await loop.run_in_executor(custom_pool, sync_db_call, user_id)
```

---

### Thread pool exhaustion when mixing sync/async

FastAPI/AnyIO default threadpool (~40) serves:
- all plain `def` endpoints
- sync `BackgroundTasks`
- `to_thread` / `run_in_threadpool` calls

If every request blocks a thread for seconds → pool saturates → new sync work queues → latency blows up (sometimes looks like “async is slow”).

**Prevent:** prefer true async I/O; limit concurrency; raise pool size deliberately; isolate heavy sync in dedicated workers; timeouts on outbound calls.

---

### CPU-bound sync work in async FastAPI

Threads don’t help much under **GIL** for pure Python CPU work. You’ll still block cores and contend.

**Better:** `ProcessPoolExecutor`, native extensions, or separate compute workers (RabbitMQ). Keep API process I/O-bound.

---

### When converting sync → async is better than thread pools

- High concurrency of I/O waits (HTTP, DB, Redis, queue)
- WebSockets / long-lived connections
- Avoiding thread-safety bugs and pool caps
- Need structured concurrency / cancellation

Example: replace `requests` with `httpx.AsyncClient` across the service.

---

### Why standard Pika is problematic in async FastAPI

**Pika** is **blocking**. Consuming/publishing on the event loop thread freezes the app.

**Options:**
1. **aio-pika** (recommended) — native async
2. Run Pika in a **dedicated thread** and bridge with thread-safe callbacks / queues
3. Separate consumer process entirely

---

### Threading + Pika vs aio-pika

| | Thread + Pika | aio-pika |
|--|---------------|----------|
| Complexity | Thread safety, bridging | Fits FastAPI naturally |
| Risk | Races, hard shutdown | Need async discipline |
| Scaling | Threads per connection | Async connections on loop |
| Fit | Legacy Pika code | Greenfield async |

Prefer **aio-pika** for FastAPI.

---

### Connection pooling for RabbitMQ in FastAPI

```python
# lifespan-managed robust connection + channel pool
from contextlib import asynccontextmanager
from aio_pika import connect_robust
from aio_pika.pool import Pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    async def get_connection():
        return await connect_robust(settings.amqp_url)

    connection_pool = Pool(get_connection, max_size=10)

    async def get_channel():
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    channel_pool = Pool(get_channel, max_size=20)
    app.state.connection_pool = connection_pool
    app.state.channel_pool = channel_pool
    yield
    await channel_pool.close()
    await connection_pool.close()

app = FastAPI(lifespan=lifespan)
```

Reuse channels carefully (QoS prefetch); often one channel per concurrent task is safer than sharing naively.

---

### Message delivery reliability strategies

- Publisher confirms / mandatory publish
- Persistent messages + durable queues
- Consumer **acks** after successful processing (`message.process()` / manual ack)
- Prefetch limits (backpressure)
- Quorum queues / mirrored queues (cluster)
- Idempotent consumers (dedupe keys)
- Dead-letter exchanges for failures
- Outbox pattern for DB + message atomicity

---

### Handling RabbitMQ connection failures

- `connect_robust` with reconnect
- Health checks that verify AMQP connectivity
- Circuit breaker on publish failures
- Buffer/fallback (local disk / secondary broker) if critical
- Alert on reconnect loops / unacked growth
- Graceful shutdown: stop consumers → wait in-flight → close

---

### Design: long-running tasks via RabbitMQ

```
POST /tasks → validate → insert Task(status=pending) → publish {task_id} → 202 + task_id
Worker consumes → status=running → do work → status=done|failed + result/error
GET /tasks/{id} → return status/result
```

**Error handling:** retries with backoff; after max → DLQ; store error on task row; optional webhook.

---

### Priority queues

- RabbitMQ priority queues (`x-max-priority`) + message `priority`
- Or separate queues (`high`, `normal`, `low`) with more consumers on high
- FastAPI sets priority from request/plan tier

---

### Dead-letter queue (DLQ) pattern

1. Main queue with `x-dead-letter-exchange`
2. Nack/`reject` without requeue on poison messages (or TTL expire)
3. Message lands in DLQ
4. Admin/replayer inspects, fixes, republishes
5. Metrics on DLQ depth

---

### Horizontal scaling of consumers

- Competing consumers on same queue (RabbitMQ round-robin)
- Stateless FastAPI/worker pods
- Prefetch tuned so one slow consumer doesn’t hog
- Don’t use exclusive queues if you need scale-out
- Idempotent handlers for at-least-once delivery

---

### Monitoring & metrics

- Queue depth, consumer count, unacked, publish rate, ack rate
- Consumer lag / time-in-queue
- Error rate, DLQ rate, reconnect count
- API: publish latency, 202 rates
- Trace IDs in message headers (propagate OpenTelemetry)

---

### Benchmark & optimize

- Load test publish path (k6/Locust)
- Measure confirm latency vs fire-and-forget
- Batch publishes where safe
- Tune prefetch, channel/connection counts
- Ensure async HTTP clients with timeouts
- Profile event-loop blocking (`blockbuster`, `aiomonitor`)

---

### Backpressure when producers outpace consumers

- Bound in-memory buffers; fail fast with 429/503
- Publisher confirms + slow down on timeout
- Limit API concurrency / rate limits
- Autoscale consumers on queue depth
- Drop/shed non-critical traffic
- Separate queues by priority

---

### Rate limiting RabbitMQ production from FastAPI

- App-level throttle (token bucket per user/IP) before publish
- Gateway rate limits
- Max in-flight publishes per process
- Return 429 when queue depth > threshold

---

### Spike exceeds cluster capacity

- Autoscale consumers/cluster
- Overflow to secondary queue/storage
- Degrade features (skip non-critical events)
- Load shed at API
- Pre-warm capacity for known peaks
- Quotas per tenant

---

### Message batching

- Buffer messages briefly (e.g. 50ms / 100 msgs) then `asyncio.gather` publishes
- Or batch in one message payload for consumers that support bulk
- Trade latency for throughput; flush on shutdown

---

### Retry strategies for failed RabbitMQ ops

- Exponential backoff + jitter on connect/publish
- Limited retries then DLQ / error state
- Distinguish transient (network) vs permanent (bad payload)
- Idempotency keys to avoid double side effects on redelivery

---

### Reprocess failed messages

- DLQ → replay tool (admin API)
- Fix bug → replay
- Store failed payloads in DB with `retry_at`
- Poison message quarantine after N failures

---

### Circuit breaker for RabbitMQ

- After N publish failures → open circuit → fail fast / queue locally
- Half-open probe after cooldown
- Libraries: `aiobreaker`, custom state machine
- Combine with timeouts

---

### Transactional DB update + RabbitMQ publish

**Problem:** DB commit without message (or vice versa) causes inconsistency.

**Outbox pattern (recommended):**
1. In same DB transaction: update business row + insert `outbox` row
2. Commit
3. Publisher process reads outbox → publishes → marks sent
4. At-least-once + idempotent consumers

Avoid distributed 2PC unless you must.

---

### Logging & alerting for RabbitMQ issues

- Structured logs: connection lost, publish fail, nack, DLQ
- Alerts: queue depth SLO, consumer = 0, DLQ > 0, reconnect storms
- Correlate `request_id` / `trace_id` / `message_id`
- Fix structlog contextvars when mixing threads/`def`/`async def` (use contextvars-aware processors; don’t rely on thread-local alone)

---

### Pub/Sub vs RPC over RabbitMQ

| | Pub/Sub | RPC |
|--|---------|-----|
| Coupling | Low | Higher (request/reply) |
| Use | Events, fanout notifications | Sync-style command needing response |
| FastAPI fit | Fire event, return 202 | Often better as HTTP; RPC adds complexity |

Use pub/sub for event-driven; HTTP/gRPC for request-response unless you need AMQP RPC.

---

### Event-driven architecture with FastAPI + RabbitMQ

- API publishes domain events (`order.created`)
- Workers/services subscribe via topic exchange routing keys
- Event versioning, idempotent handlers, outbox, observability
- FastAPI as edge; workers own heavy processing

---

### Direct vs topic exchanges

| Exchange | Routing | When |
|----------|---------|------|
| **Direct** | Exact routing key | Simple commands (`email.send`) |
| **Topic** | Pattern (`order.*`, `order.created`) | Multi-service events, flexible subscriptions |
| **Fanout** | Broadcast | Notify all consumers |

---

### Saga pattern

Long transaction split into local steps + compensating actions.

- **Choreography:** each service listens to events and emits next
- **Orchestration:** saga coordinator sends commands / listens results

Example: CreateOrder → ReserveInventory → ChargePayment → ship; on failure → ReleaseInventory, Refund.

---

### Versioning messages/events

- Include `event_type` + `schema_version` in payload/headers
- Additive changes preferred
- Consumers tolerate unknown fields
- Dual-publish during migrations
- Schema registry optional (JSON Schema/Avro)

---

### Bonus: Notification service (priority / batch / delay)

- High: dedicated queue + immediate workers (push/SMS)
- Normal: buffer in Redis lists → flush every N seconds / N items
- Delayed: per-message TTL + DLX delay pattern, or RabbitMQ delayed message plugin / scheduler

Routing key / separate exchanges by class.

---

### Exactly-once financial transactions

True exactly-once is hard. Practical approach:

- Idempotency key on API + unique constraint in DB
- Outbox for publish
- Consumer stores processed `message_id` uniquely
- At-least-once transport + **exactly-once effects** via idempotent writes
- Careful retries; no double-charge

---

### Multi-tenant SaaS isolated queues

- Queue naming: `tenant.{id}.notifications`
- Or single queue with `tenant_id` + strict isolation in code/RLS
- Per-tenant credentials/vhosts for strong isolation (costly)
- Shared FastAPI: resolve tenant from JWT → publish to tenant queue

---

### Consumers falling behind at peak

- Autoscale workers on lag
- Split hot queues; priority lanes
- Optimize handler (batch DB writes)
- Cache; reduce fanout work
- Backpressure at API
- Keep FastAPI thin: accept → persist → publish → 202

---

### Canary deployments for RabbitMQ consumers

- Deploy canary workers consuming same queue with small replica count **or** separate canary queue + % traffic publish mirror
- Health/error metrics gate promotion
- Avoid poison: version messages; canary and stable both understand schema
- Drain old pods (finish in-flight) before kill

---


## 11. Coding Problems

### Problem A: POST to third-party with exponential backoff (5xx only)

Complete decorator + FastAPI endpoint using **httpx** async (non-blocking).

```python
# retry_http.py
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    retry_on_status: range = range(500, 600),
    timeout: float = 10.0,
):
    """Retry async HTTP calls with exponential backoff on 5xx."""

    def decorator(fn: F) -> F:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    response: httpx.Response = await fn(*args, **kwargs)
                    if response.status_code in retry_on_status:
                        if attempt == max_retries:
                            return response
                        logger.warning(
                            "attempt=%s status=%s retrying in %ss",
                            attempt + 1, response.status_code, delay,
                        )
                        await asyncio.sleep(delay)
                        delay *= exponential_base
                        continue
                    return response
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        raise
                    logger.warning("attempt=%s error=%s retrying in %ss", attempt + 1, exc, delay)
                    await asyncio.sleep(delay)
                    delay *= exponential_base
            if last_exc:
                raise last_exc
            raise RuntimeError("retry logic exhausted unexpectedly")
        return wrapper  # type: ignore

    return decorator


app = FastAPI(title="Retry Demo")

class ProxyPayload(BaseModel):
    data: dict = Field(default_factory=dict)


@async_retry(max_retries=3, initial_delay=1.0, timeout=10.0)
async def post_with_retry(url: str, json_body: dict, timeout: float = 10.0) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.post(url, json=json_body)


@app.post("/proxy-status")
async def proxy_status(payload: ProxyPayload):
    """
    Calls https://httpbin.org/status/500 with retries on 5xx.
    Delays: 1s, 2s, 4s between attempts (max_retries=3 → up to 4 tries).
    """
    url = "https://httpbin.org/status/500"
    try:
        resp = await post_with_retry(url, payload.data, timeout=10.0)
    except httpx.TimeoutException:
        raise HTTPException(504, "Upstream timeout")
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Upstream error: {exc}") from exc

    if resp.status_code >= 500:
        raise HTTPException(
            502,
            detail={
                "message": "Upstream failed after retries",
                "upstream_status": resp.status_code,
            },
        )
    return {"upstream_status": resp.status_code, "body": resp.text}
```

**Interview points:** async client (doesn’t block queue), retries only 5xx (+ optional network/timeout), exponential backoff, configurable max retries/delay, proper API error mapping.

---

### Problem B: Cardless withdrawal FastAPI endpoint

Validates:
- `transaction_code`: 8 alphanumeric
- `account_number`: 11 characters
- `atm_pin_code`: 6 digits + external validation with retry on 500
- `amount`: 100–1000, multiple of 100

```python
# cardless_withdrawal.py
from __future__ import annotations

import asyncio
import logging
import re
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
app = FastAPI(title="Cardless Withdrawal API")

TXN_RE = re.compile(r"^[A-Za-z0-9]{8}$")
ACCOUNT_RE = re.compile(r"^[A-Za-z0-9]{11}$")
PIN_RE = re.compile(r"^\d{6}$")


class WithdrawalRequest(BaseModel):
    transaction_code: str = Field(..., min_length=8, max_length=8)
    account_number: str = Field(..., min_length=11, max_length=11)
    atm_pin_code: str = Field(..., min_length=6, max_length=6)
    amount: int

    @field_validator("transaction_code")
    @classmethod
    def validate_txn(cls, v: str) -> str:
        if not TXN_RE.fullmatch(v):
            raise ValueError("transaction_code must be exactly 8 alphanumeric characters")
        return v

    @field_validator("account_number")
    @classmethod
    def validate_account(cls, v: str) -> str:
        if not ACCOUNT_RE.fullmatch(v):
            raise ValueError("account_number must be exactly 11 characters")
        return v

    @field_validator("atm_pin_code")
    @classmethod
    def validate_pin_format(cls, v: str) -> str:
        if not PIN_RE.fullmatch(v):
            raise ValueError("atm_pin_code must be exactly 6 digits")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v < 100 or v > 1000:
            raise ValueError("amount must be between 100 and 1000")
        if v % 100 != 0:
            raise ValueError("amount must be a multiple of 100")
        return v


class PinValidationService:
    def __init__(self, base_url: str = "https://pin-validator.example.com"):
        self.base_url = base_url

    async def validate_pin(
        self,
        account_number: str,
        atm_pin_code: str,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> bool:
        delay = initial_delay
        url = f"{self.base_url}/validate"
        payload = {"account_number": account_number, "atm_pin_code": atm_pin_code}

        async with httpx.AsyncClient(timeout=5.0) as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, json=payload)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    if attempt == max_retries:
                        raise HTTPException(
                            status.HTTP_503_SERVICE_UNAVAILABLE,
                            "PIN service unavailable",
                        ) from exc
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue

                if resp.status_code >= 500:
                    if attempt == max_retries:
                        raise HTTPException(
                            status.HTTP_502_BAD_GATEWAY,
                            "PIN service failed after retries",
                        )
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue

                if resp.status_code == 401:
                    return False
                if resp.status_code >= 400:
                    raise HTTPException(
                        status.HTTP_502_BAD_GATEWAY,
                        f"PIN service error: {resp.status_code}",
                    )
                data = resp.json()
                return bool(data.get("valid"))

        return False


def get_pin_service() -> PinValidationService:
    return PinValidationService()


@app.post("/cardless-withdrawals")
async def cardless_withdraw(
    body: WithdrawalRequest,
    pin_service: Annotated[PinValidationService, Depends(get_pin_service)],
):
    # External PIN check with retry on 5xx — async, non-blocking
    valid = await pin_service.validate_pin(body.account_number, body.atm_pin_code)
    if not valid:
        # Do not reveal which field failed more than necessary (security)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # TODO: select_for_update account, debit, write ledger in a DB transaction
    # Never log raw PIN; mask account in logs
    logger.info(
        "withdrawal accepted txn=%s account=***%s amount=%s",
        body.transaction_code,
        body.account_number[-4:],
        body.amount,
    )

    return {
        "status": "approved",
        "transaction_code": body.transaction_code,
        "amount": body.amount,
        "currency": "INR",
    }
```

**Security best practices checklist:**
- HTTPS only; no PIN in logs/URLs
- Rate-limit endpoint; lockout after N failed PINs
- Constant-ish error messages (`Invalid credentials`)
- Idempotency-Key on withdrawal to prevent double debit
- Server-side amount limits; audit trail
- Async external calls with timeouts + 5xx retry
- DB atomic debit with row lock

---

## Quick Cheat Sheet

| Topic | One-liner |
|-------|-----------|
| FastAPI | ASGI + Pydantic + Starlette |
| Validation | Type hints → automatic 422 |
| `async def` | Event loop — must not block |
| `def` | Threadpool — OK for sync libs |
| Depends | Built-in DI |
| BackgroundTasks | After response; not for heavy jobs |
| TestClient | In-process API tests |
| CORS | `CORSMiddleware` |
| Pika in FastAPI | Prefer **aio-pika** |
| Outbox | Reliable DB + message publish |
| Retry | Exponential backoff on 5xx with httpx async |

---

*Sources: FastAPI docs (Depends, security, TestClient, CORS, WebSockets, BackgroundTasks), async correctness practices, aio-pika patterns, common messaging architecture (outbox, DLQ, sagas).*


## 1. Concurrency, Event Loop & ASGI Architecture

### Q1: How does FastAPI process `def` vs `async def` endpoints under the hood?

**Answer:** When you define an endpoint using standard `def`, FastAPI runs it inside an external thread pool (via Starlette's `anyio` worker threads) so that blocking I/O operations don't stall the main event loop. If you define it using `async def`, FastAPI invokes it directly on the main single-threaded event loop, expecting you to only execute non-blocking, asynchronous operations using `await`.

### Q2: What role does Starlette play in FastAPI, and how does it interact with ASGI servers like Uvicorn?

**Answer:** Starlette provides the core web toolkit layer—handling routing, cookie/session management, WebSockets, and low-level HTTP lifecycles. FastAPI acts as an abstraction layer over Starlette, adding Pydantic data validation, runtime serialization, dependency injection, and automatic OpenAPI documentation. Uvicorn acts as the ASGI server, listening on the socket and parsing raw HTTP/WebSocket traffic into standard ASGI event dictionaries that Starlette and FastAPI consume.

### Q3: If you must use a blocking third-party SDK inside an `async def` route handler, how do you prevent stalling the event loop?

**Answer:** Running a blocking call inside an `async def` function freezes the entire event loop, stopping all concurrent request traffic. To safely run blocking code, you must offload it to a worker thread using `anyio.to_thread.run_sync()` or the active event loop's `loop.run_in_executor()`.

### Q4: How do you implement Server-Sent Events (SSE) or streaming responses in FastAPI?

**Answer:** You utilize Starlette's `StreamingResponse`, passing it an async generator that yields chunks of bytes over time. For formal SSE, the generator should yield string data structured according to the `text/event-stream` protocol specification, allowing the client's browser `EventSource` API to process live events natively over a persistent HTTP connection.

### Q5: What are the performance and connection lifecycle implications when managing WebSockets?

**Answer:** WebSockets switch communication from stateless short-lived HTTP bursts to a stateful, persistent TCP socket connection. In FastAPI, a WebSocket route uses an async function containing an execution loop (`while True`). The runtime implication is that each active socket connection consumes a tiny fraction of memory to hold the connection state on the event loop; if your application needs to broadcast messages across isolated stateless container nodes, you must hook up an external Pub/Sub layer like Redis or RabbitMQ.

---

## 2. Dependency Injection & Request Lifecycles

### Q6: Explain the difference between `Depends()` and `Annotated[..., Depends()]`. Why is `Annotated` preferred?

**Answer:** Functionally, they behave identically. However, using `Annotated` (introduced via PEP 593) is the modern Python convention because it decouples your dependency declaration from your structural type hints. With `Annotated[DbSession, Depends(get_db)]`, type checkers and IDEs can resolve the object type directly as a clean `DbSession` rather than inferring it from a default parameter value, making code cleanly reusable outside of FastAPI (e.g., in standard unit tests).

### Q7: How does FastAPI's dependency injection system handle sub-dependency caching?

**Answer:** By default, if multiple sub-dependencies depend on the same parent dependency (such as multiple services requiring the exact same database session within a single incoming HTTP request), FastAPI caches the initial output of that parent dependency and shares the identical instance across the whole execution tree. You can override this behavior by explicitly setting `use_cache=False` inside the `Depends()` declaration.

### Q8: How do you implement a dynamic dependency that accepts runtime configuration arguments?

**Answer:** You implement it by defining a class with an `__init__` constructor that accepts configuration parameters, and a callable `__call__` method that acts as the formal dependency logic. When injected via `Depends(PermissionChecker(allowed_roles=["admin"]))`, FastAPI instantiates the object and uses the `__call__` interface to process the incoming request context.

### Q9: How can you utilize sub-dependencies to enforce structural role-based access control (RBAC) across entire APIRouters?

**Answer:** You write a dependency function that extracts user scopes from a request token, and then append this dependency to your router initialization using the `dependencies` list parameter:

```python
router = APIRouter(dependencies=[Depends(verify_admin_access)])

```

This forces all route definitions registered under that router instance to implicitly pass validation checkpoints without manually declaring the dependency inside every endpoint signature.

### Q10: How do you use the `lifespan` event handler to manage global resource lifecycles?

**Answer:** The `lifespan` context manager allows you to initialize shared, heavyweight resources (like connection pools for databases, Redis clients, or machine learning models) *before* the application begins accepting incoming web traffic. Using `yield` within the context manager marks the transition point; any teardown cleanup logic placed after the `yield` statement executes cleanly when the ASGI server triggers a shutdown signal.

### Q11: How do background tasks defined with `BackgroundTasks` differ from a distributed task queue like Celery in production?

**Answer:** `BackgroundTasks` are processed in-process on the same machine after the HTTP response is dispatched, meaning they compete for CPU and memory resources with your main web server process. For long-running, compute-heavy operations, or tasks requiring absolute persistence and retries, you should offload execution to a separate distributed worker cluster managed by tools like Celery, Arq, or RQ.

---

## 3. Pydantic Integration & Data Lifecycle

### Q12: How do you handle deep nested models in Pydantic v2 to optimize serialization speed?

**Answer:** Pydantic v2 relies on a compiled Rust core (`pydantic-core`), making serialization faster out of the box. To optimize nested model parsing, you should avoid manual deep iterations and loops; instead, make use of Pydantic’s built-in conversion parameters like `.model_dump()` or `.model_dump_json()`, and use lazy types or pre-compiled TypeAdapters for complex structural checks.

### Q13: Why should you separate Pydantic I/O schemas from your database domain models?

**Answer:** Pydantic schemas define the public API data contracts (input validation and output formatting structures), which change based on client needs, user roles, or version shifts. Database models (SQLAlchemy/Tortoise) reflect the persistent storage layout. Merging them forces internal database schemas to adapt directly to external API layouts, which breaks separation of concerns and increases the risk of exposing sensitive fields.

### Q14: How do you handle custom field validations and multi-field constraints at runtime in Pydantic?

**Answer:** For single fields, you apply the `@field_validator` decorator to run target validation logic. For complex constraints that check relationships across multiple fields (e.g., verifying that a `password_confirmation` field matches the primary `password` field), you use the `@model_validator(mode="after")` decorator to evaluate the complete object instance state.

### Q15: What is the purpose of `response_model_exclude_none` and `response_model_by_alias`?

**Answer:**

* `response_model_exclude_none=True` strips fields holding a value of `None` from the generated output dictionary, reducing JSON network payload sizes.
* `response_model_by_alias=True` forces FastAPI to serialize the JSON response using the field's external string representation (the alias) rather than the internal snake_case Python attribute names.

### Q16: How do you handle incoming file uploads via `UploadFile` without exhausting server memory?

**Answer:** Avoid using `File(bytes)`, which buffers the entire uploaded file payload directly into memory. Instead, use `UploadFile`, which leverages a SpooledTemporaryFile format under the hood—streaming larger files directly to an on-disk buffer while exposing an execution pointer via standard async stream chunks to keep memory usage minimal.

---

## 4. Advanced Middleware & Architecture Integration

### Q17: Explain the structural difference between custom Starlette middleware (`BaseHTTPMiddleware`) and pure ASGI middleware.

**Answer:** `BaseHTTPMiddleware` offers a developer-friendly high-level interface allowing you to work directly with standard `Request` and `Response` objects. However, it intercepts the request path using an internal async task group that can break context vars, stream parsing, and task state tracking. Pure ASGI middleware interfaces at a lower level by implementing a class callable that interacts directly with raw ASGI `scope`, `receive`, and `send` dictionary events.

### Q18: Why does `BaseHTTPMiddleware` sometimes cause issues with streaming responses, and how do you fix it?

**Answer:** Because `BaseHTTPMiddleware` intercepts and wraps responses, it can consume the streaming body buffer prematurely or stall chunks while managing headers. To fix this, you should avoid using `BaseHTTPMiddleware` for streaming endpoints and instead build a low-level ASGI middleware or move your interception logic into global FastAPI dependencies.

### Q19: How do you integrate OAuth2 with an external identity provider (like Auth0 or Keycloak) using FastAPI’s built-in security utilities?

**Answer:** You use FastAPI's `OAuth2AuthorizationCodeBearer` dependency to define your authorization endpoint URLs. This auto-populates security configurations inside your OpenAPI/Swagger schema definitions. Inside the dependency, you use token verification libraries (like `python-jose` or `PyJWT`) to decode the incoming token against the provider's remote JSON Web Key Sets (JWKS) to validate the signature and extract permissions.

### Q20: How do you configure a global interception pipeline for custom application validation alerts without violating clean router principles?

**Answer:** You use FastAPI's exception override handlers attached directly to the application root instance:

```python
@app.exception_handler(CustomBusinessException)
async def custom_exception_handler(request: Request, exc: CustomBusinessException):
    return JSONResponse(status_code=400, content={"error": exc.message})

```

This pattern allows routers to focus entirely on the success path, raising clear domain-specific exceptions whenever business validation fails, while leaving the final HTTP serialization structure to the centralized application boundary.

---

## 5. Database Engineering & Transaction Scoping

### Q21: How do you wire an asynchronous database session (like SQLAlchemy `AsyncSession`) into the dependency engine cleanly?

**Answer:** You implement an async generator dependency that yields a database session context inside an explicit try/finally statement blocks:

```python
async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()

```

This ensures that every individual incoming HTTP request receives an isolated database transaction boundary that cleans up after execution concludes.

### Q22: What are the architectural risks of using a single global database session instance across your web application?

**Answer:** A single global database session sharing a mutable state across asynchronous contexts creates cross-talk and connection corruption. Because multiple concurrent async tasks attempt to execute queries on the exact same socket connection simultaneously, it breaks internal transaction tracking, leaks user state across requests, and throws connection synchronization errors.

### Q23: How do you manage transaction commits and rollbacks atomically when utilizing dependencies for routing control?

**Answer:** You can wrap your session generator dependency inside a managed context transaction lifecycle block. Alternatively, you leave the commit execution entirely to your dedicated service layer/use-case objects, allowing the generator's `finally` block to execute a clean conditional rollback if unhandled exceptions escape the router layer.

### Q24: How do you implement a multi-tenant database routing paradigm in FastAPI?

**Answer:** You write a parent dependency that inspects incoming headers, subdomains, or JWT payloads to isolate a tenant identifier. This identifier is passed to a dynamic database factory dependency that fetches or generates a distinct `AsyncEngine` pool mapped to that target tenant, injecting the correct database connection into the execution context.

---

## 6. Production Engineering, Optimization & Testing

### Q25: How do you write asynchronous integration tests for a FastAPI app using HTTPX `AsyncClient`?

**Answer:** You build a testing setup utilizing `pytest-asyncio` along with HTTPX's `AsyncClient`. You initialize the client with your application instance `AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`. This allows your test code to await endpoint requests and trace full data transformations without spawning an external network port process.

### Q26: How do you bypass or override specific dependencies during unit testing pipelines?

**Answer:** You modify the application's built-in mapping dictionary via `app.dependency_overrides`. By passing your mock database context or alternative security credential generator as a replacement key:

```python
app.dependency_overrides[get_db_session] = get_mock_db_session

```

You can safely substitute real infrastructure connections with test doubles without changing any route handler signatures. Remember to clear the overrides dictionary (`app.dependency_overrides.clear()`) after your test suite runs.

### Q27: How do you optimize a FastAPI service facing heavy CPU-bound parsing while maintaining an async I/O layer?

**Answer:** You preserve your thin, non-blocking async network layer for I/O routing but push heavy CPU tasks (like intensive image transformations or large file parsing operations) out of the main process. You can offload this processing using a `ProcessPoolExecutor` via an event loop runner, or route tasks to an isolated queue architecture like Celery.

### Q28: What structural practices prevent your `APIRouter` files from turning into bloated "Fat Routers"?

**Answer:** Follow the architectural principle that routers should remain thin delivery mechanisms. Routers must focus exclusively on parsing payloads, invoking application logic, and setting return status codes. All business processing rules, validation calculations, and database mutations should live in dedicated service layers, transaction scripts, or domain use-case classes.

### Q29: How do you scale FastAPI inside a container ecosystem like Kubernetes considering Uvicorn worker settings?

**Answer:** In production container platforms like Kubernetes, it is usually cleaner to run Uvicorn as a single worker process per container container instance (`workers=1`). This allows the cluster's Horizontal Pod Autoscaler (HPA) to accurately track resource allocation based on actual CPU/Memory usage per container, rather than masking metrics behind internal multi-process worker routing topologies.

### Q30: How do you optimize response serialization performance for large JSON arrays in FastAPI?

**Answer:** If an endpoint returns massive arrays of database rows, FastAPI's default behavior—re-validating every row object against a `response_model` schema—can introduce significant CPU serialization overhead. You can optimize this by setting `response_model=None` and using database-native JSON aggregation strings directly, or using Pydantic's pre-compiled `TypeAdapter.dump_json()` utility to bypass internal processing pipelines.

---