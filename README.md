# E-commerce API (Django + DRF)

Backend-focused e-commerce REST API built with Django REST Framework, PostgreSQL, Docker, JWT authentication, Swagger documentation, automated tests, optimized queries, and transaction-safe checkout logic.

## Highlights

- JWT authentication with SimpleJWT and Djoser
- Product, category, cart, checkout, orders, and fake payment flow
- Transaction-safe checkout using `transaction.atomic()`, `select_for_update()`, `F()` expressions, and `bulk_create()`
- Query optimization using `select_related()` and `prefetch_related()`
- PostgreSQL + Docker Compose setup
- Swagger / OpenAPI documentation with drf-spectacular
- Automated tests for cart, checkout, permissions, filtering, payment, and order status transitions

---

## Tech Stack

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- Docker / Docker Compose
- SimpleJWT
- Djoser
- drf-spectacular
- django-filter
- Gunicorn
- Render

---

## Core Features

### Authentication & Users

- User registration and login
- JWT access and refresh tokens
- Authenticated user profile endpoint

### Products & Categories

- Public product and category listing
- Admin-only create, update, and delete operations
- Product filtering, searching, ordering, and pagination
- Product image and thumbnail support

### Cart & Checkout

- Add, update, remove, and clear cart items
- Stock validation before checkout
- Transaction-safe checkout process
- Stock updates handled at the database level
- Order item snapshots for price and product name

### Orders & Payment Simulation

- Authenticated users can view their own orders
- Admin users can manage order status
- Fake payment endpoint for simulating successful payment
- Controlled order status transitions

---

## Key Technical Decisions

### Transaction-safe checkout

The checkout flow uses:

- `transaction.atomic()` to keep checkout operations inside one database transaction
- `select_for_update()` to lock cart items and products during checkout
- `F()` expressions to update stock safely at the database level
- `bulk_create()` to create order items efficiently

This reduces inconsistent stock and order data during checkout.

### Query optimization

The project uses:

- `select_related('category')` for product-category queries
- `prefetch_related('items__product')` for cart items
- `prefetch_related('order_items')` for orders
- Pagination for list endpoints
- Database indexes on frequently queried fields

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

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/users/` | Register user |
| POST | `/api/v1/auth/jwt/create/` | Login and get JWT tokens |
| POST | `/api/v1/auth/jwt/refresh/` | Refresh JWT token |
| GET | `/api/v1/auth/users/me/` | Get current user |

### User Profile

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users/profile/` | Get profile |
| PUT | `/api/v1/users/profile/` | Update profile |

### Products

Current product routes are nested under `/api/v1/products/product/`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/products/product/` | List products |
| GET | `/api/v1/products/product/{id}/` | Retrieve product |
| POST | `/api/v1/products/product/` | Create product — admin only |
| PATCH | `/api/v1/products/product/{id}/` | Update product — admin only |
| DELETE | `/api/v1/products/product/{id}/` | Delete product — admin only |

Example query parameters:

```text
/api/v1/products/product/?search=iphone
/api/v1/products/product/?min_price=100&max_price=500
/api/v1/products/product/?category=electronics
/api/v1/products/product/?ordering=-price
```

### Categories

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/products/categories/` | List categories |
| POST | `/api/v1/products/categories/` | Create category — admin only |

### Cart

All cart endpoints require authentication.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/cart/` | Get current user's cart |
| POST | `/api/v1/cart/item/` | Add item to cart |
| PUT | `/api/v1/cart/item/` | Update item quantity |
| DELETE | `/api/v1/cart/item/` | Remove item from cart |
| POST | `/api/v1/cart/clear/` | Clear cart |

Example add/update item request:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

### Orders

All order endpoints require authentication.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/orders/checkout/` | Create order from cart |
| GET | `/api/v1/orders/` | List user orders |
| GET | `/api/v1/orders/{id}/` | Retrieve order |
| POST | `/api/v1/orders/{id}/pay/` | Simulate payment |
| PATCH | `/api/v1/orders/{id}/change_status/` | Change order status — admin only |

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

### 1. Clone the repository

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
```

### 3. Build and run

```bash
docker compose up -d --build
```

### 4. Create a superuser

```bash
docker exec -it django-api python manage.py createsuperuser
```

### 5. Open Swagger docs

```text
http://localhost:8000/api/docs/
```

### 6. Stop containers

```bash
docker compose down
```

---

## Run Locally Without Docker

### 1. Create and activate virtual environment

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

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### 4. Apply migrations and run server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Run Tests

```bash
python manage.py test
```

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

- Payment is simulated and does not integrate with a real payment provider.
- Product media files use local/container storage.
- Free-tier deployments may sleep or return temporary service errors.
- This project is a backend portfolio project with production-aware patterns, not a full commercial e-commerce platform.

---

## Future Improvements

- Add GitHub Actions for automated test runs
- Add API throttling and rate limiting
- Improve production static/media file handling
- Add structured logging
- Add Redis and Celery for background jobs
- Add real payment provider integration
- Add more tests for authentication and profile endpoints
- Improve category slug handling

---

## Author

Ashraf Almouaie

- GitHub: https://github.com/ashraf171
- LinkedIn: https://www.linkedin.com/in/ashraf-almouaie-77b3823bb/
- Email: ashrafalmouie@gmail.com
