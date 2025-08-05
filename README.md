# Personal Blog - Dev Mode
A subscription-based social media platform where creators share exclusive content and users subscribe to enjoy it.
<br>Full-stack application built with **Django**, **React**, and **Stripe** for seamless payment processing.
## 🔧 Tech Stack:
**Frontend:** React, JavaScript, HTML, CSS, Material UI<br>
**Backend:** Django, Python, PostgreSQL<br>
**Other Tools:** Docker, Stripe CLI, JWT Authentication, Django Email Engine<br>
## 💡 Project Overview
I was inspired by platforms like Fansly, Patreon, and Boosty, this project enables content creators to monetize their content through monthly subscriptions. Payments are handled via Stripe, integrated using the Stripe CLI.
Authentication is managed using JWT tokens, securely stored in cookies by Django. The frontend leverages Material UI to build clean, responsive user interfaces.
<br>
Real-time notifications for creators (e.g., new subscribers, likes, reports).
Email notifications for customers with subscription details using Django’s built-in email engine.

##  🚀 Lessons Learned

- I deepened my understanding of integrating external APIs by working closely with Stripe to manage recurring payments and webhooks.

- Strengthened my understanding of secure authentication using JWT tokens stored in cookies, ensuring both safety and usability without relying on localStorage.

- Wrote automated tests using Django’s TestCase and DRF’s APIClient, simulating multiple user roles (creators, subscribers, regular users).

- Practiced managing global app context and user roles in React to support different user experiences (creator vs. subscriber vs regular user).

- Gained hands-on experience with Docker for containerizing the app and preparing it for production environments.

- Developed a better mindset for end-to-end product thinking — from secure user onboarding to smooth subscription flows and user notifications.

This project wasn’t just about writing code — it was about thinking like a product engineer and building something I’d be confident deploying in the real world.


## Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- [Stripe CLI](https://docs.stripe.com/stripe-cli)
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
