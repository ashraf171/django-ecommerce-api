# E-commerce REST API

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-REST%20Framework-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Redis](https://img.shields.io/badge/Redis-Cache%20%2F%20Broker-red)
![Celery](https://img.shields.io/badge/Celery-Background%20Tasks-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![CI](https://img.shields.io/badge/GitHub%20Actions-CI-blue)

A backend-focused e-commerce API built with Django REST Framework.

The project covers product management, cart and checkout workflows, order processing, simulated payments, Redis caching, Celery background tasks, API rate limiting, Docker-based development, Swagger documentation, and automated tests.

---

## Live API

| Resource       | Link                                                       |
| -------------- | ---------------------------------------------------------- |
| Swagger UI     | https://django-ecommerce-api-gugt.onrender.com/api/docs/   |
| OpenAPI Schema | https://django-ecommerce-api-gugt.onrender.com/api/schema/ |

> The live deployment is hosted on Render. It may take a few seconds to wake up if inactive.

---

## Table of Contents

* [Features](#features)
* [Tech Stack](#tech-stack)
* [Architecture](#architecture)
* [API Endpoints](#api-endpoints)
* [Technical Highlights](#technical-highlights)
* [Run with Docker Compose](#run-with-docker-compose)
* [Run Locally](#run-locally)
* [Environment Variables](#environment-variables)
* [Tests](#tests)
* [CI](#ci)
* [Project Structure](#project-structure)
* [Known Notes](#known-notes)
* [Future Improvements](#future-improvements)

---

## Features

### Authentication

* User registration with Djoser
* JWT authentication with SimpleJWT
* Access and refresh token flow
* Authenticated user profile endpoint
* Rate-limited login endpoint

### Products and Categories

* Public product and category listing
* Product detail endpoint
* Admin-only create, update, and delete operations
* Filtering, searching, ordering, and pagination
* Product image and thumbnail support
* Redis caching for product list responses
* Cache invalidation on product create, update, and delete

### Cart and Checkout

* Add, update, remove, and clear cart items
* Stock validation before checkout
* Transaction-safe checkout flow
* Database-level stock updates
* Order item snapshots for product name and price
* Rate-limited checkout endpoint
* Background order confirmation placeholder task after successful checkout

### Orders and Payments

* Authenticated users can view their own orders
* Admin users can manage order status
* Simulated payment endpoint
* Controlled order status transitions
* Invalid status transitions are rejected

### Background Processing

* Celery configured for background tasks
* Redis used as the Celery broker
* Separate Celery worker service in Docker Compose
* Checkout triggers an asynchronous confirmation placeholder task after the database transaction commits

---

## Tech Stack

| Area              | Technology                    |
| ----------------- | ----------------------------- |
| Language          | Python 3.12                   |
| Framework         | Django, Django REST Framework |
| Database          | PostgreSQL                    |
| Cache             | Redis                         |
| Background Jobs   | Celery                        |
| Authentication    | SimpleJWT, Djoser             |
| API Documentation | drf-spectacular, Swagger UI   |
| Filtering         | django-filter                 |
| Containerization  | Docker, Docker Compose        |
| CI                | GitHub Actions                |
| Deployment        | Render                        |
| Production Server | Gunicorn                      |

---

## Architecture

```text
Client / Swagger / API Consumer
        |
        v
Django REST Framework API
        |
        |---- PostgreSQL
        |       users, products, carts, orders, stock
        |
        |---- Redis Cache
        |       product list response caching
        |
        |---- Redis Broker
                Celery task queue
                        |
                        v
                 Celery Worker
                 background task execution
```

### Docker Services

| Service  | Purpose                       |
| -------- | ----------------------------- |
| `web`    | Django REST API               |
| `db`     | PostgreSQL database           |
| `redis`  | Redis cache and Celery broker |
| `celery` | Celery background worker      |

---

## API Endpoints

### Authentication

| Method | Endpoint                    | Description                    |
| ------ | --------------------------- | ------------------------------ |
| `POST` | `/api/v1/auth/users/`       | Register user                  |
| `POST` | `/api/v1/auth/jwt/create/`  | Login and get JWT tokens       |
| `POST` | `/api/v1/auth/jwt/refresh/` | Refresh JWT token              |
| `GET`  | `/api/v1/auth/users/me/`    | Get current authenticated user |

### User Profile

| Method | Endpoint                 | Description    |
| ------ | ------------------------ | -------------- |
| `GET`  | `/api/v1/users/profile/` | Get profile    |
| `PUT`  | `/api/v1/users/profile/` | Update profile |

### Products

Product routes are currently nested under `/api/v1/products/product/`.

| Method   | Endpoint                         | Description                 |
| -------- | -------------------------------- | --------------------------- |
| `GET`    | `/api/v1/products/product/`      | List products               |
| `GET`    | `/api/v1/products/product/{id}/` | Retrieve product            |
| `POST`   | `/api/v1/products/product/`      | Create product — admin only |
| `PATCH`  | `/api/v1/products/product/{id}/` | Update product — admin only |
| `DELETE` | `/api/v1/products/product/{id}/` | Delete product — admin only |

Example query parameters:

```text
/api/v1/products/product/?search=iphone
/api/v1/products/product/?min_price=100&max_price=500
/api/v1/products/product/?category=electronics
/api/v1/products/product/?ordering=-price
```

### Categories

| Method | Endpoint                       | Description                  |
| ------ | ------------------------------ | ---------------------------- |
| `GET`  | `/api/v1/products/categories/` | List categories              |
| `POST` | `/api/v1/products/categories/` | Create category — admin only |

### Cart

All cart endpoints require authentication.

| Method   | Endpoint              | Description             |
| -------- | --------------------- | ----------------------- |
| `GET`    | `/api/v1/cart/`       | Get current user's cart |
| `POST`   | `/api/v1/cart/item/`  | Add item to cart        |
| `PUT`    | `/api/v1/cart/item/`  | Update item quantity    |
| `DELETE` | `/api/v1/cart/item/`  | Remove item from cart   |
| `POST`   | `/api/v1/cart/clear/` | Clear cart              |

Example request:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

### Orders

All order endpoints require authentication.

| Method  | Endpoint                             | Description                      |
| ------- | ------------------------------------ | -------------------------------- |
| `POST`  | `/api/v1/orders/checkout/`           | Create order from cart           |
| `GET`   | `/api/v1/orders/`                    | List user orders                 |
| `GET`   | `/api/v1/orders/{id}/`               | Retrieve order                   |
| `POST`  | `/api/v1/orders/{id}/pay/`           | Simulate payment                 |
| `PATCH` | `/api/v1/orders/{id}/change_status/` | Change order status — admin only |

---

## Technical Highlights

### Transaction-safe Checkout

Checkout is handled inside a database transaction to keep order creation, stock updates, and cart cleanup consistent.

The checkout flow uses:

* `transaction.atomic()`
* `select_for_update()`
* `F()` expressions
* `bulk_create()`

This helps prevent inconsistent stock and order data when multiple checkout requests happen at the same time.

The core checkout logic remains synchronous because it directly affects critical data such as stock, orders, and cart items.

---

### Redis Product List Caching

The product list endpoint uses Django's cache framework with Redis as the cache backend when `REDIS_URL` is available.

The cache key is based on the full request path, so different filters and query parameters generate different cache entries.

Examples:

```text
/api/v1/products/product/
/api/v1/products/product/?search=iphone
/api/v1/products/product/?category=electronics
/api/v1/products/product/?ordering=-price
```

Cache invalidation is handled when products are created, updated, or deleted.

The implementation uses cache versioning. When product data changes, the cache version is incremented, so old cached product list responses are ignored and fresh data is cached again.

If `REDIS_URL` is not provided, the project falls back to Django's local memory cache. This keeps tests and CI simple while still supporting Redis in Docker and deployed environments.

---

### Celery Background Tasks

Celery is used for non-critical background work.

Redis is used as the Celery broker. Django sends task messages to Redis, and the Celery worker consumes and executes them separately from the request-response cycle.

After a successful checkout, the application dispatches a background order confirmation placeholder task.

The task is triggered with `transaction.on_commit()`, which ensures the task is only sent after the database transaction has been committed successfully.

This avoids a common issue where a worker tries to read an order before it is fully saved.

---

### API Rate Limiting

The project uses Django REST Framework throttling with `ScopedRateThrottle`.

Configured scopes:

| Scope          | Endpoint                    | Rate      |
| -------------- | --------------------------- | --------- |
| `login`        | `/api/v1/auth/jwt/create/`  | `5/min`   |
| `checkout`     | `/api/v1/orders/checkout/`  | `10/min`  |
| `product_list` | `/api/v1/products/product/` | `100/min` |

This protects authentication, checkout, and product listing endpoints from excessive requests.

---

### Query Optimization

The project uses:

* `select_related('category')` for product-category queries
* `prefetch_related('items__product')` for cart items
* `prefetch_related('order_items')` for orders
* Pagination for list endpoints
* Database indexes on frequently queried fields

These choices reduce unnecessary database queries and improve API performance on list and detail endpoints.

---

## Order Status Flow

Allowed transitions:

```text
PENDING -> PAID -> SHIPPED -> DELIVERED
PENDING -> CANCELED
PAID -> CANCELED
FAILED -> PENDING
```

Invalid transitions are blocked by the API.

---

## Run with Docker Compose

### 1. Clone the Repository

```bash
git clone https://github.com/ashraf171/django-ecommerce-api.git
cd django-ecommerce-api
```

### 2. Create `.env`

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

POSTGRES_DB=ecommerce_db
POSTGRES_USER=ecommerce_user
POSTGRES_PASSWORD=ecommerce_password

DATABASE_URL=postgres://ecommerce_user:ecommerce_password@db:5432/ecommerce_db

REDIS_URL=redis://redis:6379/1

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3. Build and Start Services

```bash
docker compose up -d --build
```

This starts:

* Django API
* PostgreSQL database
* Redis cache / Celery broker
* Celery worker

### 4. Apply Migrations

```bash
docker compose exec web python manage.py migrate
```

### 5. Create a Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Check Containers

```bash
docker ps
```

Expected containers:

```text
django-api
postgres-db
redis-cache
celery-worker
```

### 7. Check Redis

```bash
docker compose exec redis redis-cli ping
```

Expected output:

```text
PONG
```

### 8. Check Celery

```bash
docker compose logs celery
```

Expected worker status:

```text
celery ready
```

### 9. Open API Documentation

```text
http://localhost:8000/api/docs/
```

### 10. Stop Services

```bash
docker compose down
```

To remove containers and volumes, including PostgreSQL data:

```bash
docker compose down -v
```

Use `down -v` carefully because it deletes database volume data.

---

## Run Locally

### 1. Create and Activate Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

For a simple local setup with SQLite:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

Redis is optional in this mode. If `REDIS_URL` is not provided, the project falls back to Django's local memory cache.

To use Redis locally, run Redis and add:

```env
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Apply Migrations and Run Server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 5. Run Celery Worker Locally

If Redis is running locally and Celery environment variables are configured:

```bash
celery -A E_commerce worker -l info
```

On Windows:

```bash
celery -A E_commerce worker -l info --pool=solo
```

---

## Environment Variables

| Variable                | Description               | Example                                   |
| ----------------------- | ------------------------- | ----------------------------------------- |
| `SECRET_KEY`            | Django secret key         | `your-secret-key`                         |
| `DEBUG`                 | Django debug mode         | `True`                                    |
| `ALLOWED_HOSTS`         | Allowed hosts             | `localhost,127.0.0.1`                     |
| `DATABASE_URL`          | Database connection URL   | `postgres://user:password@db:5432/dbname` |
| `REDIS_URL`             | Redis cache URL           | `redis://redis:6379/1`                    |
| `CELERY_BROKER_URL`     | Celery broker URL         | `redis://redis:6379/0`                    |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://redis:6379/0`                    |
| `POSTGRES_DB`           | PostgreSQL database name  | `ecommerce_db`                            |
| `POSTGRES_USER`         | PostgreSQL username       | `ecommerce_user`                          |
| `POSTGRES_PASSWORD`     | PostgreSQL password       | `ecommerce_password`                      |

---

## Tests

Run tests locally:

```bash
python manage.py test
```

Run tests inside Docker:

```bash
docker compose exec web python manage.py test
```

The test suite covers:

* Product filtering, searching, ordering, and permissions
* Redis product list caching
* Cache invalidation on product create, update, and delete
* Cart operations
* Checkout and stock validation
* Celery task dispatch after checkout
* Order listing and permissions
* Payment simulation
* Order status transitions
* API rate limiting for product list, checkout, and login

---

## CI

GitHub Actions runs the test suite on push and pull requests to `main`.

The workflow:

* Checks out the repository
* Sets up Python
* Installs dependencies
* Applies migrations
* Runs Django tests

The CI environment can run without Redis by falling back to Django's local memory cache.

---

## Project Structure

```text
django-ecommerce-api/
├── E_commerce/          # Django settings, Celery app, and root URLs
├── users/               # User profile API
├── product/             # Product and category APIs
├── cart/                # Cart models, serializers, views, and checkout service
├── orders/              # Orders, status flow, payment simulation, and Celery tasks
├── screenshots/         # API screenshots
├── Dockerfile
├── docker-compose.yml
├── build.sh
├── manage.py
├── requirements.txt
└── README.md
```

---

## Screenshots

Swagger documentation screenshot:

```text
screenshots/swagger.png
```

---

## Known Notes

* Payment is simulated and does not integrate with a real payment provider.
* Order confirmation is currently represented by a background placeholder task, not a real email provider.
* Product media files use local/container storage.
* Redis is used as a cache layer and Celery broker, not as the primary database.
* PostgreSQL remains the source of truth for users, products, carts, orders, and stock.
* Free-tier deployments may sleep or return temporary service errors.
* This is a backend portfolio project, not a full commercial e-commerce platform.

---

## Future Improvements

* Add real email provider integration for order confirmations
* Add Celery Beat for scheduled tasks
* Improve production static and media file handling
* Add structured logging
* Add real payment provider integration
* Add more tests for authentication and profile endpoints
* Improve production Redis configuration
* Add test coverage reporting
* Add object storage for media files

---

## Author

Ashraf Almouaie

* GitHub: https://github.com/ashraf171
* LinkedIn: https://www.linkedin.com/in/ashraf-almouaie/
* Email: [ashrafalmouie@gmail.com](mailto:ashrafalmouie@gmail.com)
