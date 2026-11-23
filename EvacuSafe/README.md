# EvacuSafe

**Disaster-Adaptive Evacuation Center Management & Real-Time Resource Tracking System.**
Production-ready Django vertical-sliced architecture backed by Supabase PostgreSQL, role-based authorization, live polling synchronization, audit logging, and incident/resource management.

## System Architecture

```text
proj/
├── manage.py
├── .env.example              # Documented environment template
├── requirements.txt          # Production dependencies (Django, psycopg2, whitenoise, gunicorn)
├── Procfile                  # Production process runner for Render/Heroku
├── apps/                     # Vertical slice architecture
│   ├── home/                 # Live Dashboard, Evacuation Centers, Audit Logs, Incidents, Resources
│   ├── login/                # Authentication slice (login, logout, session security)
│   ├── register/             # User registration slice
│   ├── profile/              # Responder profile, avatar upload, role management, account admin
│   └── user_settings/        # Notification preferences, language localization, password reset/change
├── static/                   # Static assets (CSS, JS, SVG icons)
├── templates/                # Centralized templates organized by app slice
│   ├── base.html             # Common app shell, navigation, responsive sidebar, flash alerts
│   ├── home/home.html        # Live operational map, real-time sync, center list & inventory
│   ├── login/                # Login and password recovery views
│   ├── profile/profile.html  # Profile management & account administration
│   └── user_settings/        # User settings & security controls
└── config/                   # Core Django project configuration
    ├── settings.py           # Production-hardened settings with Supabase & test isolation
    ├── urls.py               # Root URL configuration
    ├── wsgi.py               # WSGI entrypoint for Gunicorn
    └── asgi.py               # ASGI entrypoint
```

## Setup & Local Development

1. **Clone repository and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Provide your Supabase connection URI in `DATABASE_URL` (or leave blank / set `USE_SQLITE=True` for offline local development).

3. **Verify and apply migrations:**
   ```bash
   python manage.py check
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create administrator account:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run test suite:**
   ```bash
   python manage.py test
   ```
   *Note: Automated tests run against an isolated in-memory SQLite database and never modify your production Supabase database.*

6. **Start development server:**
   ```bash
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Security & Production Features

- **Strict Role-Based Access Control (RBAC):** Distinct permissions for `Viewer/Responder`, `Coordinator`, and `Admin` users.
- **Audit Trails & Soft Deletion:** Full change history tracking old vs. new capacity/occupancy and status with archivable center lifecycle.
- **Capacity Safeguards:** Model- and form-level validations preventing negative or overflow occupancy with automatic 100% capacity flagging.
- **Live Background Sync:** Real-time polling endpoint (`/api/centers/live/`) dynamically synchronizing status counters and map markers without full page reloads.
- **Incident & Resource Tracking:** Active disaster disaster logging with severity ratings and center relief supply monitoring.
- **WhiteNoise Asset Serving:** Direct, optimized static file delivery configured for containerized and cloud deployments.
