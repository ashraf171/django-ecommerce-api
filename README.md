# E-commerce API (Django + DRF)

🌐 Live API:
https://django-ecommerce-api-gugt.onrender.com


![Django](https://img.shields.io/badge/Django-DRF-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-blue)
![Python](https://img.shields.io/badge/Python-3.12-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)
![Status](https://img.shields.io/badge/status-production-brightgreen)
![Render](https://img.shields.io/badge/deployed-render-blue)


A scalable e-commerce REST API built with Django, DRF, and PostgreSQL.



---

## 📌 Overview

The API supports full e-commerce workflow from authentication to order lifecycle management.
This project is a production-ready REST API deployed on Render using Docker and PostgreSQL.


## Features

* JWT authentication (SimpleJWT)
* User management using Djoser
* Product and category management
* Cart system (add, update, delete, clear)
* Checkout process with stock validation
* Order system with status management
* Cancel order with stock restoration
* Filtering, search, and ordering
* Fake payment endpoint for simulating order payment
* Permission handling (user vs admin)
* Automated tests (25 tests)

---

## Tech Stack

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- Docker

---
## 📦 Architecture

Monolithic Django REST API containerized with Docker and deployed on Render.
----

## 🔐 Security

- JWT authentication
- Permission-based access control
- Environment variables for sensitive data



---
## Run with Docker Compose
This setup works in both local and production environments.
### Build and start containers
```bash
docker compose up -d --build
```
### Apply database migrations
```bash
docker exec -it django-api python manage.py migrate
```

### Create superuser
```bash
docker exec -it django-api python manage.py createsuperuser
```
### Check running containers
```bash
docker ps
```
### Stop containers
```bash
docker compose down
```
### Stop and remove volumes (reset database)
```bash
docker compose down -v
```
### Rebuild project from scratch
```bash
docker compose up -d --build
```
### Swagger Docs

```text
Swagger Docs:
- Local: http://localhost:8000/api/docs/
- Production: https://django-ecommerce-api-gugt.onrender.com/api/docs/
```

## API Structure

### Authentication

* POST `/api/v1/auth/users/` – register
* POST `/api/v1/auth/jwt/create/` – login
* POST `/api/v1/auth/jwt/refresh/` – refresh token
* GET `/api/v1/auth/users/me/` – current user

---

### Profile

* GET `/api/v1/users/profile/`
* PUT `/api/v1/users/profile/`

---

### Products

* GET `/api/v1/products/`

Supports:

* search: `?search=iphone`
* filtering: `?min_price=100&max_price=500`
* category: `?category=electronics`
* ordering: `?ordering=-price`

---

### Cart

* GET `/api/v1/cart/`
* POST `/api/v1/cart/items/`
* PUT `/api/v1/cart/items/`
* DELETE `/api/v1/cart/items/`
* POST `/api/v1/cart/clear/`

---
### Orders

- GET `/api/v1/orders/`
- GET `/api/v1/orders/{id}/`
- POST `/api/v1/orders/{id}/pay/`
- PATCH `/api/v1/orders/{id}/change_status/`
---

## Order Status Flow

Valid transitions:

```
PENDING → PAID → SHIPPED → DELIVERED
PENDING → CANCELED
PAID → CANCELED
```

Invalid transitions are blocked.

---

### Payment Flow

- Orders are created with `PENDING` status.
- A pending order can be paid using:
- POST `/api/v1/orders/{id}/pay/`
- After successful payment, the order status becomes `PAID`.
- Paid orders can then be shipped by admin.

## Quick Start

### Installation

```bash
git clone <your-repo-url>
cd django-ecommerce-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Database

```bash
python manage.py migrate
```

---

## Run Server

```bash
python manage.py runserver
```

---

## Run Tests

```bash
python manage.py test
```

---

## Notes

* Checkout is wrapped in database transactions to avoid inconsistent data
* Stock updates are handled safely to prevent race conditions
* Permissions are enforced so users can only access their own data

---

## Future Improvements

* Real payment integration (Stripe)
* Add Redis caching
* Add CI/CD pipeline

## 🚀 Deployment

- Platform: Render
- Containerized: Docker
- Database: PostgreSQL


## API Documentation

Swagger UI:

![Swagger Screenshot](screenshots/swagger.png)