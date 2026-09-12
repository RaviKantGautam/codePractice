### what is the name of library to access aws?
boto3

### what is the library used in flask and fastapi as orm?
sqlalchemy

### what is the new fastapi supports in the model?
SQLModel which is build on top of sqlalchemy

### how to find the last data in the table from the django orm query?
user = User.objects.all().last()

### how many type of serializers are in django?
Serializer, ModelSerializer, HyperlinkedModelSerializer, ListSerializer

### what is the command run in production to start django server?
1. gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
2. python -m uvicorn myproject.asgi:application --host 0.0.0.0 --port 8000

### what is dependency injection in python?
Dependency Injection (DI) is a design pattern where a function or object receives the external resources (dependencies) it needs from the outside, rather than creating them internally

In Python, this is achieved by passing dependent objects as arguments into a class initializer (__init__) or a function, instead of hardcoding imports or instantiations inside them. By separating the creation of a resource from its usage, your code becomes loosely coupled, highly modular, and significantly easier to test using mocks.

### How to get query params in django?
search_query = request.GET.get('q')
category = request.query_params.get('category')

### how to get specific fields in modelserializer in django?

from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # Explicitly declare only the specific fields you need
        fields = ['id', 'name', 'price'] 

### in fastapi when to use async function and when not ?

When to use async def
Use async def if your endpoint or dependency performs I/O-bound operations (like waiting for a database, a network request, or a third-party API) AND you are using a library that supports the await keyword. [1] (https://www.youtube.com/watch?v=2JPDt-Jp6fM&t=1633), [2] (https://www.logiclooptech.dev/fastapi-async-vs-sync-when-to-use-each-benchmarks-and-real-world-tips/)Async Databases: When utilizing async clients like asyncpg, databases, Motor (MongoDB), or SQLAlchemy’s async engine.External API Calls: When using non-blocking HTTP clients like HTTPX AsyncClient or aiohttp.Async Tasks / Utilities: When you want to fire operations in parallel using tools like asyncio.gather().Trivial Endpoints: Simple routes like /health check endpoints that just return a static JSON string or status code. [1] (https://hughesadam87.medium.com/dead-simple-when-to-use-async-in-fastapi-0e3259acea6f), [2] (https://santhop.medium.com/boosting-fastapi-performance-by-embracing-async-i-o-part-one-a34c6289b42b), [3] (https://www.youtube.com/watch?v=1z8LLSZSWHM&t=457), [4] (https://www.logiclooptech.dev/fastapi-async-vs-sync-when-to-use-each-benchmarks-and-real-world-tips/), [5] (https://pub.towardsai.net/v-fastapi-leverage-the-async-when-and-why-8a52462ddd9c)

When NOT to use async def (Use normal def)
Use standard def when your endpoint uses synchronous, blocking libraries, or when it handles heavy mathematical/computational tasks. [1] (https://global.moneyforward-dev.jp/2025/06/06/fastapi-async-a-small-keyword-with-huge-impact/), [2] (https://leapcell.io/blog/asynchronous-vs-synchronous-functions-in-fastapi-when-to-pick-which)If you use async def with blocking code, it freezes the entire application's single-threaded event loop, preventing all other users from getting responses. [1] (https://santhop.medium.com/boosting-fastapi-performance-by-embracing-async-i-o-part-one-a34c6289b42b), [2] (https://pub.towardsai.net/v-fastapi-leverage-the-async-when-and-why-8a52462ddd9c)Synchronous Database Drivers: Traditional usage of psycopg2, standard Django/SQLAlchemy ORM without async configuration, or sqlite3.Blocking HTTP Clients: Using the popular requests library or urllib.CPU-Bound Tasks: Heavy calculations, data transformations, image processing (Pillow), or cryptography.File System I/O: Standard Python file functions (open(), os.path) are inherently blocking.When in Doubt: If you aren't sure how a library behaves under the hood, use standard def. [1] (https://fastapi.tiangolo.com/async/), [2] (https://www.reddit.com/r/FastAPI/comments/18c66xt/how_do_you_decide_which_functionsroutes_should_be/), [3] (https://shiladityamajumder.medium.com/async-apis-with-fastapi-patterns-pitfalls-best-practices-2d72b2b66f25), [4] (https://santhop.medium.com/boosting-fastapi-performance-by-embracing-async-i-o-part-one-a34c6289b42b), [5] (https://www.youtube.com/watch?v=2JPDt-Jp6fM&t=1633), [6] (https://leapcell.io/blog/asynchronous-vs-synchronous-functions-in-fastapi-when-to-pick-which), [7] (https://www.logiclooptech.dev/fastapi-async-vs-sync-when-to-use-each-benchmarks-and-real-world-tips/), [8] (https://pub.towardsai.net/v-fastapi-leverage-the-async-when-and-why-8a52462ddd9c)


### what are the types of worker in celery to run?
prefork
eventlet and gevent
threads
solo

### what is the difference between task and shared_task in celery?
The core difference between @app.task and @shared_task in Celery is how they bind to a Celery application instance. While @app.task requires you to explicitly import and use a concrete Celery app instance, @shared_task creates a reusable task without relying on a specific app instance.
Use @shared_task if you are working with Django, creating a library, or splitting your application into distinct, reusable packages.
Use @app.task if you are building a simple, standalone script or a fast API where everything lives in a single module and you do not anticipate needing to reuse the code elsewhere

