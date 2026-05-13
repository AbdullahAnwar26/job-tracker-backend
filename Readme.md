# Job Tracker & Application Management API

Production-ready backend system for tracking job applications, reminders, notes, resume uploads, and analytics.

Built using Django REST Framework, PostgreSQL, Redis, Celery, Docker, JWT Authentication, and OpenAPI documentation.

---

# Features

* JWT Authentication
* OTP Email Verification
* Secure Login & Logout
* Job Application Tracking
* Company Management
* Resume & File Uploads
* Notes & Reminder System
* User Analytics Dashboard
* Redis + Celery Background Tasks
* Swagger/OpenAPI Documentation
* Dockerized Deployment Setup
* PostgreSQL Database Integration
* Token Rotation & Blacklisting
* Production-Ready Configuration

---

# Tech Stack

* Python
* Django
* Django REST Framework
* PostgreSQL
* Redis
* Celery
* Celery Beat
* Docker
* Gunicorn
* JWT Authentication
* drf-spectacular (Swagger/OpenAPI)

---

# System Architecture

```text
Client → Django REST API → PostgreSQL

Background Tasks:
Celery → Redis → Email/Reminder Processing
```

---

# Authentication Flow

1. User signs up using email
2. OTP is sent to the registered email
3. User verifies OTP
4. JWT access and refresh tokens are generated
5. Protected APIs are accessed using Bearer Token authentication

---

# API Documentation

Swagger/OpenAPI Documentation:

```text
/api/docs/
```

ReDoc Documentation:

```text
/api/redoc/
```

---

# Core Modules

## Authentication

* User Registration
* OTP Verification
* JWT Login
* Token Refresh
* Logout & Token Blacklisting

## Job Tracking

* Add and manage companies
* Add and manage jobs
* Track application status
* Store notes for applications
* Upload resumes and supporting documents

## Reminder System

* Schedule reminders
* Background reminder processing using Celery
* Periodic task execution using Celery Beat

## Analytics

* User application analytics
* Dashboard statistics
* Status-based insights

---

# Local Development Setup

## Clone Repository

```bash
git clone <your-repository-url>
cd job-tracker-backend
```

---

## Create Environment Variables

Create a `.env` file using `.env.example`

---

## Run with Docker

```bash
docker-compose up --build
```

Application runs on:

```text
http://localhost:8000
```

---

# Environment Variables

```env
DEBUG=False

SECRET_KEY=your-secret-key

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password

REDIS_URL=redis://redis:6379/0

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

# Celery Background Tasks

Implemented background tasks:

* OTP cleanup task
* Reminder scheduler
* Background email processing

---

# Docker Services

The project runs using the following containers:

* Django Web
* PostgreSQL
* Redis
* Celery Worker
* Celery Beat

---

# API Highlights

* RESTful API Design
* Pagination Support
* Secure JWT Authentication
* Protected Endpoints
* File Upload Support
* OpenAPI Schema Generation
* Production-ready Docker Configuration

---

# Production Readiness

Configured for deployment using:

* Docker
* Gunicorn
* PostgreSQL
* Redis
* Celery
* Environment Variables
* Static File Collection
* Swagger/OpenAPI Documentation

---

# Future Improvements

* CI/CD pipeline using GitHub Actions
* Kubernetes deployment support
* Real-time notifications
* AI-powered resume analysis
* Email notification templates
* Advanced analytics dashboard
* Role-based access control (RBAC)

---

# Screenshots

Create a `screenshots/` folder and add:

* Swagger Documentation
* Docker Containers Running
* Celery Worker Logs
* API Response Examples

Example:

```text
screenshots/
├── swagger.png
├── docker.png
├── celery.png
```

---

# License

MIT License
