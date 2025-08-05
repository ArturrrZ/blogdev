# Personal Blog — Dev Mode

Full-stack web application built with **Django** (backend), **React** (frontend), and **Stripe** for payments.  
Development and deployment are managed via **Docker**.

---

## Features

- Django REST API backend
- React frontend (Vite + MUI)
- Stripe payment integration
- JWT authentication for secure API access
- Dockerized dev environment
- Hot reload for backend and frontend
- Environment variables for easy config

---

## Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ArturrrZ/blogdev
cd blogdev
```

### 2. Configure environment variables

Rename `.env.example` to `.env` and fill in your secrets:


Edit `.env` and set:

- Django secret key
- Stripe keys
- Email credentials
- Database config

### 3. Build and start containers

```bash
docker-compose -f docker-compose.dev.yml up --build
```

- Django API: [http://localhost:8000](http://localhost:8000)
- React frontend: [http://localhost:3000](http://localhost:3000)

### 4. Apply migrations

```bash
docker-compose exec backend python manage.py migrate
```

### 5. Create superuser (optional)

```bash
docker-compose exec backend python manage.py createsuperuser
```

---

## Stripe Integration

- Set Stripe keys in `.env`
- Use Stripe CLI for webhook testing:
  ```bash
  stripe listen --forward-to localhost:8000/api/webhooks/stripe/
  ```
- Webhook secret goes in `.env` as `STRIPE_WEBHOOK_SECRET`

---

## Development Workflow

- **Backend**: Edit code in `backend/` — auto-reloads in container
- **Frontend**: Edit code in `frontend/` — auto-reloads in container
- **Docker**: Containers rebuild on code changes

---

## Useful Commands

- Stop containers: `docker-compose -f docker-compose.dev.yml down`
- Rebuild containers: `docker-compose -f docker-compose.dev.yml up --build`
- Run tests: `docker-compose exec backend python manage.py test`

---
