# 🏟️ Sports Field Rental Platform

A RESTful API built with **Django** and **Django REST Framework** for managing the rental of football fields and other sports facilities.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [User Roles](#user-roles)
- [Authentication](#authentication)
- [Contributing](#contributing)

---

## 📌 Overview

This platform allows users to browse and book sports fields (football, volleyball, basketball, tennis, etc.), while complex managers can manage their venues and admins oversee the entire system.

---

## ✨ Features

- 🔐 Role-based access control (User, Complex Manager)
- 🔐 Using Django Grouping feature for defining Admin Group 
- 📅 Field reservation and booking management
- 🏢 Sports complex and field management
- 📊 Admin dashboard for full system control
- 🔍 Filter and search available fields by date, time, and sport type
- 📱 RESTful API ready for web and mobile clients

---

## 🛠️ Tech Stack

| Layer        | Technology                     |
|-------------|-------------------------------|
| Language     | Python 3.11+                  |
| Framework    | Django 5.1.3                    |
| API          | Django REST Framework (DRF)   |
| Database     | PostgreSQL                    |
| Auth         | JWT (SimpleJWT) 5.5.1               |
| Doc          | drf-spectacular (Swagger/OpenAPI) |
| django filters | Fliters and search 25.1          |
| celery         | async tasks proccess 5.4.0   |
| django-phonenumber-field | phonenumber field 8.4.0  |
---

## 📁 Project Structure

```
Sport_booking/
│
├── backend/                  # Project settings and URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
|   ├── asgi.py  
|   ├── apps/
|       ├── accounts/                # User management & authentication
│       │    ├── models.py
│       │    ├── views.py
│       │    ├── serializers.py
│       │    ├── urls.py
|       │    ├── tests.py
|       │    ├── signals.py
|       │    ├── admin.py
|       │    ├── backends.py  
|       │    └── apps.py
|       │ 
│       │ 
|       └── bookings/
|       |    ├── admin.py  
|       |    ├── apps.py
|       |    ├── models.py
|       |    ├── tests.py
|       |    ├── views.py
|       |    ├── serializers.py
|       |    └── urls.py
│       |
|       |
|       |
|       └── venues/               # Sports complex and venues management
│       |    ├── models.py
│       |    ├── views.py
│       |    ├── serializers.py
│       |    ├── urls.py
|       |    ├── admin.py
|       |    └── tests.py
|       |      
|       | 
|       |
|       └── notifications/               # notifications management system   
│           ├── models.py
│           ├── views.py
│           ├── serializers.py
│           └── urls.py
|           └── tests.py
│
|
│
├── logs/
|   ├── errors.log
|   └── user_signup.log
|   
|
│
├── requirements.txt
├── .env
├── manage.py
├── ARCHITECTURE.md
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/amir-hash19/sport_booking.git
cd Sport_Booking

# Create and activate virtual environment
python -m venv env
source env/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

---

## 🔑 Environment Variables

Create a `.env` file based on `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

DB_NAME=sport_booking
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/token/` | Refresh token  | Public |
| POST | `/api/v1/token/verify/` |  check JWT token | Public |
| POST | `/api/v1/user/signup/` | register user | Public |
|POST | `/api/v1/user/login/` | login user | Public |

### Complexes
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/complexes/` | List all complexes | Public |
| POST | `/api/complexes/` | Create a complex | Complex Manager |
| GET | `/api/complexes/{id}/` | Complex detail | Public |
| PUT | `/api/complexes/{id}/` | Update complex | Complex Manager |
| DELETE | `/api/complexes/{id}/` | Delete complex | Admin |

### Fields
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/fields/` | List all fields | Public |
| POST | `/api/fields/` | Add a field | Complex Manager |
| GET | `/api/fields/{id}/` | Field detail | Public |
| PUT | `/api/fields/{id}/` | Update field | Complex Manager |
| DELETE | `/api/fields/{id}/` | Delete field | Admin |

### Reservations
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/reservations/` | List user reservations | User |
| POST | `/api/reservations/` | Create reservation | User |
| GET | `/api/reservations/{id}/` | Reservation detail | User/Admin |
| DELETE | `/api/reservations/{id}/` | Cancel reservation | User/Admin |

> 📄 Full interactive API documentation available at `/api/schema/swagger-ui/` after running the server.

---

## 👥 User Roles and Admin Group

| Role or Group | Description | Permissions |
|------|-------------|-------------|
| **Admin** | Full system access | Manage all users, complexes, fields, reservations |
| **Complex Manager** | Venue owner/operator | Create and manage own complexes and fields, view reservations for their fields |
| **User** | Regular customer | Browse fields, make and cancel reservations |

---

## 🔐 Authentication

This API uses **JWT (JSON Web Token)** authentication via `djangorestframework-simplejwt`.

Include the token in your request headers:

```http
Authorization: Bearer <your_access_token>
```

Token expiry:
- Access token: 3 hour
- Refresh token: 5 days

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

```bash
# Create a new branch
git checkout -b feature/your-feature-name

# Make your changes and commit
git commit -m "feat: add your feature description"

# Push and open a Pull Request
git push origin feature/your-feature-name
```

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/amir-hash19">Amir Hosein</a>
</div>