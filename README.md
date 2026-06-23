# E-commerce API (Django + DRF)

Backend-focused e-commerce REST API built with Django REST Framework, PostgreSQL, Redis, Docker, JWT authentication, Swagger/OpenAPI documentation, GitHub Actions CI, automated tests, optimized queries, Redis caching, and transaction-safe checkout logic.

---

## Highlights

* JWT authentication with SimpleJWT and Djoser
* Product, category, cart, checkout, orders, and fake payment flow
* Transaction-safe checkout using `transaction.atomic()`, `select_for_update()`, `F()` expressions, and `bulk_create()`
* Query optimization using `select_related()` and `prefetch_related()`
* Redis caching for product list API responses
* Cache invalidation when products are created, updated, or deleted
* PostgreSQL + Redis + Docker Compose setup
* Swagger / OpenAPI documentation with drf-spectacular
* GitHub Actions CI for automated test runs
* Automated tests for cart, checkout, permissions, filtering, payment, order status transitions, and Redis cache behavior

---

## Tech Stack

* Python 3.12
* Django
* Django REST Framework
* PostgreSQL
* Redis
* Docker / Docker Compose
* SimpleJWT
* Djoser
* drf-spectacular
* django-filter
* django-redis
* Gunicorn
* GitHub Actions
* Render

---

## Core Features

### Authentication & Users

* User registration and login
* JWT access and refresh tokens
* Authenticated user profile endpoint

### Products & Categories

* Public product and category listing
* Admin-only create, update, and delete operations
* Product filtering, searching, ordering, and pagination
* Product image and thumbnail support
* Redis caching for product list responses
* Cache invalidation on product create, update, and delete

### Cart & Checkout

* Add, update, remove, and clear cart items
* Stock validation before checkout
* Transaction-safe checkout process
* Stock updates handled at the database level
* Order item snapshots for price and product name

### Orders & Payment Simulation

* Authenticated users can view their own orders
* Admin users can manage order status
* Fake payment endpoint for simulating successful payment
* Controlled order status transitions

---

## Key Technical Decisions

### Transaction-safe Checkout

The checkout flow uses:

* `transaction.atomic()` to keep checkout operations inside one database transaction
* `select_for_update()` to lock cart items and products during checkout
* `F()` expressions to update stock safely at the database level
* `bulk_create()` to create order items efficiently

This reduces inconsistent stock and order data during checkout.

### Query Optimization

The project uses:

* `select_related('category')` for product-category queries
* `prefetch_related('items__product')` for cart items
* `prefetch_related('order_items')` for orders
* Pagination for list endpoints
* Database indexes on frequently queried fields

### Redis Product List Caching

The product list endpoint uses Django's cache framework with Redis as the cache backend when `REDIS_URL` is available.

The product list response is cached to reduce repeated database queries and improve API response performance for frequently requested product listing pages.

The cache key is based on the full request path, so different query parameters generate different cache entries.

Examples:

```text
/api/v1/products/product/
/api/v1/products/product/?search=iphone
/api/v1/products/product/?category=electronics
/api/v1/products/product/?ordering=-price
```

Cache invalidation is handled when products are created, updated, or deleted. The implementation uses cache versioning, so stale cached product lists are avoided after product data changes.

The project falls back to Django's local memory cache when `REDIS_URL` is not provided. This keeps the test and CI environment simple while still allowing Redis caching in Docker/local environments.

---

## API Documentation

Swagger UI is available here:

```text
Live:
https://django-ecommerce-api-gugt.onrender.com/api/docs/

Local:
http://127.0.0.1:8000/api/docs/
```

OpenAPI schema:

```text
Live:
https://django-ecommerce-api-gugt.onrender.com/api/schema/

Local:
http://127.0.0.1:8000/api/schema/
```

> Note: The live deployment is hosted on Render. It may take a few seconds to wake up if inactive.

---

## Main API Endpoints

### Authentication

| Method | Endpoint                    | Description              |
| ------ | --------------------------- | ------------------------ |
| POST   | `/api/v1/auth/users/`       | Register user            |
| POST   | `/api/v1/auth/jwt/create/`  | Login and get JWT tokens |
| POST   | `/api/v1/auth/jwt/refresh/` | Refresh JWT token        |
| GET    | `/api/v1/auth/users/me/`    | Get current user         |

### User Profile

| Method | Endpoint                 | Description    |
| ------ | ------------------------ | -------------- |
| GET    | `/api/v1/users/profile/` | Get profile    |
| PUT    | `/api/v1/users/profile/` | Update profile |

### Products

Current product routes are nested under `/api/v1/products/product/`.

| Method | Endpoint                         | Description                 |
| ------ | -------------------------------- | --------------------------- |
| GET    | `/api/v1/products/product/`      | List products               |
| GET    | `/api/v1/products/product/{id}/` | Retrieve product            |
| POST   | `/api/v1/products/product/`      | Create product — admin only |
| PATCH  | `/api/v1/products/product/{id}/` | Update product — admin only |
| DELETE | `/api/v1/products/product/{id}/` | Delete product — admin only |

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
| GET    | `/api/v1/products/categories/` | List categories              |
| POST   | `/api/v1/products/categories/` | Create category — admin only |

### Cart

All cart endpoints require authentication.

| Method | Endpoint              | Description             |
| ------ | --------------------- | ----------------------- |
| GET    | `/api/v1/cart/`       | Get current user's cart |
| POST   | `/api/v1/cart/item/`  | Add item to cart        |
| PUT    | `/api/v1/cart/item/`  | Update item quantity    |
| DELETE | `/api/v1/cart/item/`  | Remove item from cart   |
| POST   | `/api/v1/cart/clear/` | Clear cart              |

Example add/update item request:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

### Orders

All order endpoints require authentication.

| Method | Endpoint                             | Description                      |
| ------ | ------------------------------------ | -------------------------------- |
| POST   | `/api/v1/orders/checkout/`           | Create order from cart           |
| GET    | `/api/v1/orders/`                    | List user orders                 |
| GET    | `/api/v1/orders/{id}/`               | Retrieve order                   |
| POST   | `/api/v1/orders/{id}/pay/`           | Simulate payment                 |
| PATCH  | `/api/v1/orders/{id}/change_status/` | Change order status — admin only |

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
```

### 3. Build and Run

```bash
docker compose up -d --build
```

This starts:

* Django API
* PostgreSQL database
* Redis cache

### 4. Check Running Containers

```bash
docker ps
```

Expected services:

```text
django-api
postgres-db
redis-cache
```

### 5. Test Redis Connection

```bash
docker compose exec redis redis-cli ping
```

Expected output:

```text
PONG
```

### 6. Apply Migrations

```bash
docker compose exec web python manage.py migrate
```

### 7. Create a Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 8. Open Swagger Docs

```text
http://localhost:8000/api/docs/
```

### 9. Stop Containers

```bash
docker compose down
```

To remove containers and volumes, including PostgreSQL data:

```bash
docker compose down -v
```

Use `down -v` carefully because it deletes database volume data.

---

## Run Locally Without Docker

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

If you want to use Redis locally outside Docker, run Redis on your machine and add:

```env
REDIS_URL=redis://localhost:6379/1
```

### 4. Apply Migrations and Run Server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Run Tests

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
* Order listing and permissions
* Payment simulation
* Order status transitions

---

## CI with GitHub Actions

This project includes a GitHub Actions workflow that runs automated tests on push and pull requests to `main`.

The CI workflow:

* Checks out the repository
* Sets up Python
* Installs dependencies
* Applies migrations
* Runs Django tests

The CI environment uses test environment variables and can run without Redis by falling back to Django's local memory cache.

---

## Project Structure

```text
django-ecommerce-api/
├── E_commerce/          # Django project settings and root URLs
├── users/               # Custom user profile API
├── product/             # Product and category APIs
├── cart/                # Cart models, serializers, views, and checkout service
├── orders/              # Orders, order items, status flow, and payment simulation
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
* Product media files use local/container storage.
* Redis is used as a cache layer, not as the primary database.
* PostgreSQL remains the source of truth for products, orders, users, cart data, and stock.
* Free-tier deployments may sleep or return temporary service errors.
* This project is a backend portfolio project with production-aware patterns, not a full commercial e-commerce platform.

---

## Future Improvements

* Add Celery with Redis for background jobs
* Add API throttling and rate limiting
* Improve production static/media file handling
* Add structured logging
* Add real payment provider integration
* Add more tests for authentication and profile endpoints
* Improve deployment configuration for production Redis
* Add coverage reporting

---

## Author

Ashraf Almouaie

* GitHub: https://github.com/ashraf171
* LinkedIn: https://www.linkedin.com/in/ashraf-almouaie-77b3823bb/
* Email: [ashrafalmouie@gmail.com](mailto:ashrafalmouie@gmail.com)
