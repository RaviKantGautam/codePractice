# Flask Interview Questions & Answers

> Interview prep covering Flask core concepts, blueprints, SQLAlchemy, auth, deployment, contexts, signals, and scenario-based questions.

---

## Table of Contents

1. [Core Comparison & Architecture](#1-core-comparison--architecture)
2. [Blueprints, Factory, Views & Context](#2-blueprints-factory-views--context)
3. [Database, Migrations & Transactions](#3-database-migrations--transactions)
4. [Auth, Forms, Validation & Files](#4-auth-forms-validation--files)
5. [WSGI, Deployment & Async](#5-wsgi-deployment--async)
6. [General Flask Q&A](#6-general-flask-qa)
7. [Validation Libraries Comparison](#7-validation-libraries-comparison)
8. [Scenario-Based Questions](#8-scenario-based-questions)

---

## 1. Core Comparison & Architecture

### Difference between Flask and other frameworks like Django?

| Aspect | **Flask** | **Django** | **FastAPI** |
|--------|-----------|------------|-------------|
| Philosophy | Microframework — minimal core, choose extensions | Batteries-included full stack | API-first, async + Pydantic |
| Routing | Decorators / blueprints | `urls.py` | Decorators + type hints |
| ORM | Optional (SQLAlchemy via extension) | Built-in ORM | Optional |
| Admin | Add Flask-Admin | Built-in admin | N/A / custom |
| Templates | Jinja2 | Django templates | Not primary focus |
| Async | Possible (newer Flask) but traditionally sync/WSGI | Sync + ASGI options | Async-first ASGI |
| Best for | APIs, microservices, custom stacks | CMS, large products, rapid full apps | High-perf APIs |

**Flask pros:** flexible, lightweight, easy to learn, great for APIs/microservices.  
**Flask cons:** you assemble security, admin, forms, etc. yourself — more decisions, more room for inconsistency.

---

### How do you handle database interactions in Flask?

Common stack:

| Tool | Role |
|------|------|
| **Flask-SQLAlchemy** | ORM integration with Flask |
| **SQLAlchemy** (core/ORM) | Queries, models, engine |
| **Flask-Migrate / Alembic** | Schema migrations |
| **psycopg / asyncpg** | Postgres drivers |
| Raw **DB-API** | Rare; for simple scripts |

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)

# create
u = User(email="a@b.com")
db.session.add(u)
db.session.commit()

# read
User.query.filter_by(email="a@b.com").first()
```

---

### Atomic transactions in Flask

Use SQLAlchemy session transactions:

```python
from sqlalchemy.exc import SQLAlchemyError

def transfer(from_id, to_id, amount):
    try:
        with db.session.begin():  # commits on success, rolls back on error
            a = db.session.get(Account, from_id, with_for_update=True)
            b = db.session.get(Account, to_id, with_for_update=True)
            if a.balance < amount:
                raise ValueError("Insufficient funds")
            a.balance -= amount
            b.balance += amount
    except Exception:
        db.session.rollback()
        raise

# Or explicit
try:
    db.session.add(...)
    db.session.commit()
except SQLAlchemyError:
    db.session.rollback()
    raise
```

Nested: SQLAlchemy savepoints (`begin_nested()`). Keep transactions short; don’t hold locks across external HTTP calls.

---

## 2. Blueprints, Factory, Views & Context

### Flask Blueprints — what and why?

A **Blueprint** is a modular set of routes, templates, static files, and error handlers that you **register** on the app.

```python
# auth/routes.py
from flask import Blueprint, render_template

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login")
def login():
    return render_template("auth/login.html")

# app factory
def create_app():
    app = Flask(__name__)
    from auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp)
    return app
```

**Use when:** large apps, feature modules (`auth`, `api`, `admin`), reusable plugins, separating concerns, avoiding one giant `app.py`.

---

### Application Factory

**Application factory** = function (`create_app`) that builds and returns a configured `Flask` instance instead of a single global `app`.

```python
# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# __init__.py
def create_app(config_object="config.ProdConfig"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    db.init_app(app)
    migrate.init_app(app, db)

    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    return app
```

**Benefits:** multiple apps (test/prod configs), no circular imports with `init_app`, easier testing (`create_app("config.TestConfig")`).

---

### Function vs class-based views

| | **Function views** | **Class-based views (MethodView / View)** |
|--|--------------------|-------------------------------------------|
| Style | `@bp.route` + function | Class with `get`/`post` methods |
| Reuse | Decorators | Inheritance / mixins |
| Simple CRUD | Very clear | Good when methods share setup |

```python
from flask.views import MethodView

class UserAPI(MethodView):
    def get(self, user_id):
        return {"id": user_id}

    def post(self):
        return {"created": True}, 201

bp.add_url_rule("/users/<int:user_id>", view_func=UserAPI.as_view("user"))
bp.add_url_rule("/users", view_func=UserAPI.as_view("users"))
```

Prefer functions for simple endpoints; MethodView/Flask-RESTful Resource for structured APIs.

---

### Application Context vs Request Context

| Context | Proxies | Lifetime | Purpose |
|---------|---------|----------|---------|
| **Application context** | `current_app`, `g` | App handling / explicit `app.app_context()` | Access config, extensions without importing `app` |
| **Request context** | `request`, `session` | One HTTP request | Current request data & session |

```python
from flask import current_app, g, request

with app.app_context():
    print(current_app.config["SECRET_KEY"])

# During a request:
# request.method, session["user_id"], g.db
```

`g` = request/app-context local storage (not cross-request). For cross-request user data use `session` or DB.

CLI/`flask shell` often needs `app.app_context()` for DB access.

---

### Signals

**Flask signals** (via Blinker) notify listeners when events happen — loose coupling.

Built-in-ish patterns: `request_started`, `request_finished`, `got_request_exception`; Flask-SQLAlchemy model signals; custom signals.

```python
from blinker import Namespace
my_signals = Namespace()
user_registered = my_signals.signal("user-registered")

def send_welcome(sender, user, **extra):
    send_email(user.email, "Welcome!")

user_registered.connect(send_welcome)

# after creating user
user_registered.send(current_app._get_current_object(), user=user)
```

**Use when:** audit logs, cache invalidation, emails after register — without hard-wiring views to those side effects.

---

## 3. Database, Migrations & Transactions

### SQLAlchemy integration

```python
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app
```

Query (2.x style often via `db.session.execute(select(...))`; classic `Model.query` still common with Flask-SQLAlchemy).

---

### Database migration — Alembic / Flask-Migrate

**Flask-Migrate** wraps **Alembic** for Flask.

```bash
flask db init
flask db migrate -m "add users table"
flask db upgrade
flask db downgrade
```

Ensure models are **imported** so Alembic detects them. With factory pattern: `migrate.init_app(app, db)` inside `create_app`. For existing DBs: generate initial migration against empty DB then `flask db stamp head`.

---

## 4. Auth, Forms, Validation & Files

### User authentication and authorization

| Library | Role |
|---------|------|
| **Flask-Login** | Session user (`current_user`, `@login_required`) |
| **Flask-Principal / custom decorators** | Roles/permissions |
| **Flask-JWT-Extended / PyJWT** | JWT APIs |
| **Flask-Security-Too / Authlib** | Higher-level auth |

```python
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@bp.route("/login", methods=["POST"])
def login():
    user = User.query.filter_by(email=request.form["email"]).first()
    if user and user.check_password(request.form["password"]):
        login_user(user)
        return redirect(url_for("main.index"))
    flash("Invalid credentials")
    return redirect(url_for("auth.login"))
```

Authorization: role checks (`@roles_required("admin")`) or `if not current_user.is_admin: abort(403)`.

---

### Form validation

| Tool | Use |
|------|-----|
| **Flask-WTF + WTForms** | Server-rendered forms + CSRF |
| **Marshmallow / Pydantic** | JSON API validation |
| Manual `request.form` checks | Tiny forms only |

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired(), Length(min=8)])

@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # save user
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)
```

---

### File uploads

```python
import os
from werkzeug.utils import secure_filename
from flask import request, current_app

ALLOWED = {"png", "jpg", "pdf"}

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

@bp.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f or f.filename == "":
        abort(400)
    if not allowed(f.filename):
        abort(400)
    name = secure_filename(f.filename)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], name)
    f.save(path)
    return {"filename": name}, 201
```

Config: `MAX_CONTENT_LENGTH` to cap size. For huge files: direct-to-S3 / chunked uploads (see scenarios).

---

## 5. WSGI, Deployment & Async

### Flask + Gunicorn / uWSGI

Flask is a **WSGI** app (`app` callable). Production servers:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "myapp:create_app()"
uwsgi --http :8000 --wsgi-file wsgi.py --callable app --processes 4
```

**Benefits:** multi-process concurrency, graceful restarts, better than Flask dev server, sits behind Nginx for TLS/static files.

```
Client → Nginx → Gunicorn/uWSGI → Flask app
```

---

### Deploying Flask to production

1. `create_app` + config via env (`SECRET_KEY`, `DATABASE_URL`)
2. `DEBUG=False`, strong `SECRET_KEY`
3. Gunicorn/uWSGI + Nginx
4. Migrations on release (`flask db upgrade`)
5. Docker image + health check
6. HTTPS, secure cookies, `ProxyFix` if behind proxy
7. Logging to stdout; metrics; CI/CD
8. Optional: blue-green / rolling deploys

---

### Asynchronous tasks in Flask

Flask request handlers are typically **sync**. For background work:

| Tool | Use |
|------|-----|
| **Celery** + Redis/RabbitMQ | Standard distributed tasks |
| **RQ** | Simpler Redis queue |
| **APScheduler** | Cron-like jobs |
| **threading** | Tiny fire-and-forget (not for prod scale) |

```python
# tasks.py
from celery import shared_task

@shared_task
def send_email_task(to, subject, body):
    ...

# view
send_email_task.delay(user.email, "Welcome", "Hello")
```

---

### Example of a complex Flask app (interview story)

**Example narrative:** multi-tenant SaaS API — blueprints for `auth`, `billing`, `projects`; Flask-SQLAlchemy + Migrate; Celery for invoices/PDFs; Flask-JWT for mobile; RBAC; S3 uploads.

**Challenges & solutions:**
- Circular imports → application factory + blueprints
- Long reports blocking workers → Celery
- Schema evolution → Alembic; expand/contract migrations
- N+1 queries → `joinedload` / explicit joins
- Secret sprawl → env + vault; never commit secrets

---


## 6. General Flask Q&A

### How does routing work in Flask?

`@app.route()` / `@bp.route()` maps URL rules to view callables. Supports converters (`<int:id>`, `<uuid:id>`), methods, and `url_for` reverse routing.

```python
@app.route("/users/<int:user_id>", methods=["GET", "PATCH"])
def user_detail(user_id):
    ...
```

---

### Explain templates in Flask

Flask uses **Jinja2**. Templates live in `templates/`; pass context from views.

```html
<!-- templates/hello.html -->
<h1>Hello {{ name }}</h1>
{% for item in items %}
  <li>{{ item }}</li>
{% endfor %}
```

```python
return render_template("hello.html", name="Ravi", items=items)
```

Auto-escapes HTML by default (XSS mitigation).

---

### Purpose of `__init__.py`

Marks a directory as a **Python package** so you can `import myapp`. In Flask projects it often holds `create_app()` and package-level exports. (In Python 3.3+ namespace packages can omit it, but Flask apps still conventionally use it.)

---

### How Flask manages configuration

```python
app.config.from_object("config.ProductionConfig")
app.config.from_envvar("MYAPP_SETTINGS")
app.config.from_mapping(SECRET_KEY=os.environ["SECRET_KEY"])
app.config["SQLALCHEMY_DATABASE_URI"] = "..."
```

Use class-based configs (`Dev`, `Test`, `Prod`) + env overrides. Never hardcode secrets.

---

### Role of Werkzeug

**Werkzeug** is the WSGI toolkit under Flask: routing, request/response objects, debugging, `secure_filename`, test client utilities, local proxies. Flask is essentially a thin layer over Werkzeug + Jinja2 + Click.

---

### What is Flask-WTF?

Extension integrating **WTForms** with Flask: form classes, CSRF protection (via secret key), file fields, `validate_on_submit()`.

---

### Handling form submission

```python
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        email = request.form.get("email")
        message = request.form.get("message")
        # validate & save
        flash("Thanks!")
        return redirect(url_for("contact"))
    return render_template("contact.html")
```

Prefer Flask-WTF for CSRF + validators.

---

### Flask-SQLAlchemy

Flask extension that wires SQLAlchemy engine/session to the app, provides `db.Model`, `db.session`, and request-scoped session handling patterns.

---

### Error handling

```python
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return {"error": "internal"}, 500
```

Also `abort(403)`. API apps often return JSON error handlers.

---

### Middleware in Flask

Flask doesn’t use Django-style middleware list primarily; common patterns:

1. **WSGI middleware** wrapping the app
2. `@app.before_request` / `@app.after_request` / `@app.teardown_request`
3. ProxyFix, custom WSGI class

```python
@app.before_request
def load_user():
    g.request_id = request.headers.get("X-Request-ID", uuid4().hex)

@app.after_request
def add_header(response):
    response.headers["X-Request-ID"] = g.request_id
    return response
```

```python
class TimingMiddleware:
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        # log timing, then:
        return self.app(environ, start_response)

app.wsgi_app = TimingMiddleware(app.wsgi_app)
```

---

### Flask-SocketIO

Adds **WebSocket** (and long-polling fallback) support for real-time apps (chat, live dashboards). Often with `eventlet`/`gevent` or message queue for multi-process.

```python
from flask_socketio import SocketIO, emit
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on("message")
def handle_message(data):
    emit("message", data, broadcast=True)
```

---

### Testing support

```python
import pytest
from myapp import create_app

@pytest.fixture
def client():
    app = create_app("config.TestConfig")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_home(client):
    rv = client.get("/")
    assert rv.status_code == 200
```

Use `test_request_context()` for unit-testing code that needs `request`.

---

### Purpose of Flask extensions — examples

Reusable packages that call `init_app(app)`:

- Flask-SQLAlchemy, Flask-Migrate
- Flask-Login, Flask-WTF, Flask-Mail
- Flask-CORS, Flask-Limiter
- Flask-RESTful / Flask-Smorest
- Flask-SocketIO, Flask-Caching

---

### Implement user authentication (summary)

Flask-Login + hashed passwords (Werkzeug `generate_password_hash` / `check_password_hash`) + HTTPS + secure cookie settings + CSRF on forms. For APIs: JWT bearer tokens.

---

### Flask-RESTful advantages

- Resource classes mapped to URLs
- Clean HTTP method handlers (`get`, `post`, …)
- Request parsing helpers
- Consistent API structure

```python
from flask_restful import Api, Resource
api = Api(app)

class UserResource(Resource):
    def get(self, user_id):
        return {"id": user_id}

api.add_resource(UserResource, "/users/<int:user_id>")
```

Modern alternatives: Flask + Marshmallow, or migrate to FastAPI for new APIs.

---

### `url_for`

Builds URLs from endpoint names — avoids hardcoding paths.

```python
url_for("auth.login")
url_for("static", filename="css/app.css")
url_for("user_detail", user_id=5, _external=True)
```

---

### Static files

Put assets in `static/`. Serve via:

```html
<link href="{{ url_for('static', filename='css/style.css') }}">
```

In production, often Nginx serves `/static` directly for performance.

---

### `before_request` and `after_request`

- **before_request:** auth gate, open DB, set `g.*`, reject bad hosts
- **after_request:** add headers, log status (must return response)
- **teardown_request:** close resources even on exceptions

---

### `flash` and `session`

- **`session`:** signed cookie (or server-side) dict across requests — needs `SECRET_KEY`
- **`flash`:** store one-time messages in session for next request; consume with `get_flashed_messages()` in templates

---

### Secret key — why important?

Signs session cookies and CSRF tokens (Flask-WTF). Weak/leaked key → session forgery / CSRF bypass. Load from env; rotate carefully.

---

### Blue-green deployment with Flask

Run **Blue** (current) and **Green** (new) environments behind a load balancer. Deploy/test Green, switch traffic, keep Blue for rollback. Flask apps are stateless workers — perfect for this if sessions are sticky-safe (signed cookies or shared Redis sessions) and DB migrations are backward compatible.

---

### Securing Flask against common vulnerabilities

- `SECRET_KEY`, `SESSION_COOKIE_SECURE`, `HTTPONLY`, `SAMESITE`
- CSRF (Flask-WTF) for browsers
- Escape templates (default); sanitize markdown/HTML
- Parameterized ORM queries (avoid raw SQL string format)
- AuthZ on every sensitive route
- `MAX_CONTENT_LENGTH`; validate uploads
- Rate limiting (Flask-Limiter)
- Keep deps updated; `DEBUG=False` in prod
- Security headers (Talisman)

---


## 7. Validation Libraries Comparison

### Pydantic vs Marshmallow vs Cerberus

| | **Pydantic** | **Marshmallow** | **Cerberus** |
|--|--------------|-----------------|--------------|
| Style | Type hints / models (v2 very fast) | Schema classes | Dict schema rules |
| Serialization | Excellent | Excellent | Validation-focused |
| Ecosystem | FastAPI native; growing Flask use | Classic Flask APIs | Lightweight configs |
| Nested/complex | First-class | First-class | Good for documents |
| Coercion | Strong | Configurable | Limited vs others |

**Flask tip:** Marshmallow historically common with Flask-RESTful/Smorest; Pydantic works well for new JSON APIs; Cerberus for simple rule dicts / config validation.

---

## 8. Scenario-Based Questions

### Scenario: Handling User Authentication

**Design:**
1. `User` model with email + `password_hash`
2. Registration: validate → hash password → save → optional email verify
3. Login: verify hash → `login_user()` → regenerate session
4. Logout: `logout_user()`; clear session
5. `@login_required` on protected views
6. HTTPS; secure cookies; CSRF on forms; lockout / rate limit login
7. APIs: issue JWT access + refresh instead of session cookies

```python
from werkzeug.security import generate_password_hash, check_password_hash

user.password_hash = generate_password_hash(password)
check_password_hash(user.password_hash, password)
```

---

### Scenario: Large file uploads (GBs)

**Don’t stream multi-GB through Flask workers.**

**Approach:**
1. **Direct-to-cloud:** frontend requests presigned S3/GCS URL → uploads directly → callback to API with object key
2. Or **chunked / resumable** uploads (tus protocol) with a dedicated upload service
3. Set reverse-proxy body limits carefully; disable buffering where needed
4. Virus scan async via queue after upload complete
5. Store metadata in DB; never hold entire file in memory (`stream` to disk only if unavoidable)
6. Frontend: show progress; retry chunks

---

### Scenario: Role-Based Access Control (RBAC)

```python
from functools import wraps
from flask import abort
from flask_login import current_user

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles and not current_user.is_admin:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@bp.route("/admin/users")
@roles_required("admin")
def admin_users():
    ...
```

Models: `Role`, `Permission`, M2M `user_roles`. Check permissions in decorators or Flask-Principal. Never trust client-sent role fields.

---

### Scenario: Real-time communication

Use **Flask-SocketIO**:
- Events: `connect`, `disconnect`, `join_room`, domain events
- Redis message queue so multiple Gunicorn workers share pub/sub
- Auth on connect (session cookie or token)
- Fallback long-polling if needed

Alternatively for new greenfield realtime: separate FastAPI/Node WS service.

---

### Scenario: Database schema changes without downtime

**Expand/contract pattern:**
1. Add new columns/tables (nullable) — migrate forward
2. Deploy code that writes both old+new (or dual-read)
3. Backfill data
4. Switch reads to new schema
5. Deploy code that stops writing old
6. Drop old columns in later migration

Tools: **Flask-Migrate/Alembic**. Avoid destructive changes in same release as code that still needs old columns. Blue-green + backward-compatible migrations.

---

### Scenario: Blue-Green deployment

1. Blue serving v1; deploy v2 to Green
2. Run migrations (compatible)
3. Smoke test Green (internal URL)
4. Switch LB to Green
5. Monitor; rollback = switch back to Blue
6. Drain Blue connections

Shared DB must stay compatible with both versions during cutover. Session store shared (Redis) if sticky sessions aren’t used.

---

### Scenario: Concurrent requests / heavy load

- Multiple Gunicorn workers/threads (threads help for I/O-bound)
- Connection pooling to DB; PgBouncer
- Caching (Redis/Flask-Caching) for hot reads
- Celery for slow tasks — keep request path short
- CDN for static
- Avoid global locks; use DB transactions carefully
- Load test (Locust/k6); profile N+1 and slow queries
- Horizontally scale stateless app replicas behind LB

---

### Scenario: API with Flask-RESTful

```python
from flask import Flask
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app, prefix="/api/v1")

class ContactList(Resource):
    def get(self):
        return [{"id": 1, "name": "Ada"}]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", required=True, type=str)
        parser.add_argument("email", required=True, type=str)
        args = parser.parse_args()
        # create...
        return args, 201

class Contact(Resource):
    def get(self, contact_id):
        return {"id": contact_id}

    def put(self, contact_id):
        return {"id": contact_id, "updated": True}

    def delete(self, contact_id):
        return "", 204

api.add_resource(ContactList, "/contacts")
api.add_resource(Contact, "/contacts/<int:contact_id>")
```

Structure by resources; version prefix; auth decorators; Marshmallow for complex schemas.

---

### Scenario: Internationalization (i18n) / Localization (l10n)

- **Flask-Babel**: mark strings with `_()`, extract, translate `.po/.mo`
- Detect locale: user preference → `Accept-Language` → default
- Localize dates/numbers/currency
- Separate locale per request in `before_request` (`g.locale`)
- Store user language preference in profile/session

```python
from flask_babel import Babel, _

babel = Babel(app)
@app.route("/")
def index():
    return _("Hello, World!")
```

---

### Scenario: Securing the application (XSS, SQLi, CSRF)

| Threat | Mitigation |
|--------|------------|
| **SQL injection** | ORM/bound parameters; never f-string SQL with user input |
| **XSS** | Jinja autoescape; sanitize rich text; CSP headers |
| **CSRF** | Flask-WTF CSRFToken; SameSite cookies |
| **Session hijack** | Secure/HttpOnly cookies; HTTPS; regenerate session on login |
| **Auth bypass** | Explicit checks on every route; deny by default |
| **Upload abuse** | Type/size allowlists; store outside web root / S3 |
| **Deps** | Pin & scan vulnerabilities |

Use **Flask-Talisman** for HTTPS + security headers.

---

## Quick Cheat Sheet

| Topic | One-liner |
|-------|-----------|
| Flask vs Django | Micro vs batteries-included |
| Blueprint | Modular routes package |
| Application factory | `create_app()` for config/test isolation |
| App context | `current_app`, `g` |
| Request context | `request`, `session` |
| Flask-Migrate | Alembic wrapper for schema changes |
| Atomic txn | `db.session.commit()` / `begin()` + rollback |
| Flask-Login | Session authentication |
| Flask-WTF | Forms + CSRF |
| Gunicorn | Production WSGI server |
| Celery/RQ | Async background jobs |
| Signals | Decoupled event notifications |
| `url_for` | Reverse URL building |
| Secret key | Signs sessions/CSRF |

---

*Sources: Flask docs (blueprints, contexts, factories), Miguel Grinberg Mega-Tutorial patterns, Flask-Migrate/Alembic practices, common production WSGI deployment.*
