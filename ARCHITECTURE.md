# 🏗️ Architecture Overview — SportBooking

This document describes the system architecture, design decisions, and data flow of the **SportBooking** platform.

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Tech Stack](#tech-stack)
- [Application Structure](#application-structure)
- [Database Design](#database-design)
- [Authentication Flow](#authentication-flow)
- [Request Lifecycle](#request-lifecycle)
- [Role & Permission Design](#role--permission-design)
- [Design Decisions](#design-decisions)

---

## 🌐 System Overview

```
                        ┌─────────────────────────────────┐
                        │           Client Layer          │
                        │  Mobile App / Web App / Postman │
                        └────────────────┬────────────────┘
                                         │ HTTPS
                                         ▼
                        ┌─────────────────────────────────┐
                        │         Django Application      │
                        │                                 │
                        │  ┌──────────┐  ┌─────────────┐  │
                        │  │  DRF API │  │ Django Admin│  │
                        │  └────┬─────┘  └──────┬──────┘  │
                        │       │               │         │
                        │  ┌────▼───────────────▼──────┐  │
                        │  │         URL Router        │  │
                        │  └────────────────┬──────────┘  │
                        │                   │             │
                        │  ┌────────────────▼──────────┐  │
                        │  │     App Layer (4 Apps)    │  │
                        │  │  accounts |   venues      │  │
                        │  │  bookings | notifications │  |
                        │  └────────────────┬──────────┘  │
                        │                   │             │
                        │  ┌────────────────▼──────────┐  │
                        │  │         ORM Layer         │  │
                        │  └────────────────┬──────────┘  │
                        └───────────────────┼─────────────┘
                                            │
                        ┌───────────────────▼─────────────┐
                        │        sqlite/PostgreSQL DB     │
                        └─────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.11+ | Core language |
| Framework | Django 5.x | Web framework |
| API | Django REST Framework | RESTful API |
| Auth | SimpleJWT | JWT token management |
| Database | PostgreSQL | Primary data store |
| Admin | Django Admin | Management dashboard |
| Docs | drf-spectacular | Swagger / OpenAPI |

---

## 📦 Application Structure

The project is divided into **4 Django apps**, each with a single responsibility:

### 1. `accounts` — User Management
- Custom User model with role field (`admin`, `user`, `complex_manager`)
- Registration, login, logout
- JWT token issue and refresh
- Profile management

### 2. `complexes` — Sports Complex Management
- CRUD for sports complexes
- Each complex is owned by a `complex_manager`
- Contains metadata: name, location, description, working hours

### 3. `fields` — Field Management
- Individual fields (football, basketball, volleyball, etc.)
- Each field belongs to a complex
- Contains: field type, capacity, price per hour, availability schedule

### 4. `reservations` — Booking System
- Users create reservations for specific fields and time slots
- Handles conflict detection (double booking prevention)
- Reservation status: `pending`, `confirmed`, `cancelled`

---

## 🗄️ Database Design

```
┌─────────────────────┐         ┌──────────────────────┐
│       Useraccount   │         │      Venue           |
│─────────────────────│         │──────────────────────│
│ id (PK)             │    ┌───▶│ id (PK)              │
│ name                |    |    | manager ForeignKey   |
| last_name           |    │    │ venue_name           │
│ email               │    │    │ description          |  
| is_active           |    |    │    |    | address              
│ password            │    │    │ manager (FK → User)  │
│ is_manager          |    |────┘    │ working_hours   │
│ phone_number        |                                |
| national_id         |      │         │ created_at    │
│ created_at          │         └──────────┬───────────┘
└─────────────────────┘                    │
           │                               │ 1
           │                               ▼ N
           │                    ┌──────────────────────┐
           │                    │        Field          │
           │                    │──────────────────────│
           │                    │ id (PK)               │
           │                    │ complex (FK)          │
           │                    │ name                  │
           │                    │ field_type            │
           │                    │ price_per_hour        │
           │                    │ capacity              │
           │                    │ is_active             │
           │                    └──────────┬───────────┘
           │                               │
           │ 1                             │ 1
           ▼ N                             ▼ N
┌──────────────────────────────────────────────────────┐
│                    Reservation                        │
│──────────────────────────────────────────────────────│
│ id (PK)                                               │
│ user (FK → User)                                      │
│ field (FK → Field)                                    │
│ date                                                  │
│ start_time                                            │
│ end_time                                              │
│ status  [pending | confirmed | cancelled]             │
│ total_price                                           │
│ created_at                                            │
└──────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication Flow

JWT-based authentication using `djangorestframework-simplejwt`:

```
User                         API Server                    DB
 │                               │                          │
 │── POST /auth/login/ ─────────▶│                          │
 │   {email, password}           │── validate credentials ─▶│
 │                               │◀─ user object ───────────│
 │◀─ {access, refresh} ───────── │                          │
 │                               │                          │
 │── GET /api/reservations/ ────▶│                          │
 │   Authorization: Bearer <JWT> │                          │
 │                               │── decode & verify JWT    │
 │                               │── check role/permission  │
 │◀─ 200 OK + data ───────────── │                          │
 │                               │                          │
 │── POST /auth/token/refresh/ ─▶│                          │
 │   {refresh_token}             │── validate refresh token │
 │◀─ {new access token} ──────── │                          │
```

**Token TTL:**
- Access Token: `3 hour`
- Refresh Token: `5 days`

---

## 🔄 Request Lifecycle

```
Incoming Request
      │
      ▼
 Django Middleware
 (CORS, Auth, Security)
      │
      ▼
 URL Router (urls.py)
      │
      ▼
 JWTAuthentication
 (verify token → attach user)
      │
      ▼
 Permission Classes
 (IsAdmin / IsComplexManager / IsUser)
      │
      ▼
 View / ViewSet
      │
      ▼
 Serializer (validate + serialize)
      │
      ▼
 Model / ORM Query
      │
      ▼
 PostgreSQL
      │
      ▼
 JSON Response
```

---

## 👥 Role & Permission Design

| Action | Admin | Complex Manager | User |
|--------|-------|----------------|------|
| Manage all users | ✅ | ❌ | ❌ |
| Create complex | ✅ | ✅ | ❌ |
| Edit own complex | ✅ | ✅ | ❌ |
| Delete any complex | ✅ | ❌ | ❌ |
| Add field to complex | ✅ | ✅ (own) | ❌ |
| View all reservations | ✅ | ✅ (own fields) | ❌ |
| Create reservation | ✅ | ❌ | ✅ |
| Cancel own reservation | ✅ | ❌ | ✅ |
| Access Django Admin | ✅ | ❌ | ❌ |

**Custom Permission Classes:**

```python
# permissions.py

class IsComplexManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'is_complex_manager'

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.role == 'admin'
```

---

## 💡 Design Decisions

### 1. Custom User Model
Used a custom `AbstractBaseUser` with a `role` field instead of Django groups, for simpler and more explicit role checking across the codebase.

### 2. Conflict Detection for Reservations
Before confirming a reservation, the system queries for overlapping bookings on the same field and time slot:

```python
overlapping = Reservation.objects.filter(
    field=field,
    date=date,
    status__in=['pending', 'confirmed'],
    start_time__lt=end_time,
    end_time__gt=start_time
)
if overlapping.exists():
    raise ValidationError("This time slot is already booked.")
```

### 3. Soft Relations via FK
Reservations reference both `User` and `Field` via ForeignKey with `on_delete=PROTECT` to prevent accidental data loss when a field is deactivated.

### 4. Price Calculation
`total_price` is calculated and stored at reservation time (not computed dynamically) to preserve historical pricing even if field prices change later.

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.