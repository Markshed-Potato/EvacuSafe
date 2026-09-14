# EvacuSafe

Disaster-Adaptive Evacuation Center Management & Real-Time Resource Tracking System.
Django project using vertical slicing, backed by Supabase PostgreSQL.

## Project structure

```
proj/
├── manage.py
├── .env
├── requirements.txt
├── apps/                     # every vertical slice lives here
│   ├── login/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── register/
│   │   └── ... (same shape)
│   ├── home/
│   │   └── ... (Live Dashboard — EvacuationCenter model)
│   ├── profile/
│   │   └── ... (avatar, role, phone, bio)
│   └── user_settings/
│       └── ... (notifications, dark mode, language, password change)
├── static/
│   ├── css/
│   │   ├── base.css          # shared design tokens + layout chrome
│   │   ├── login/login.css
│   │   ├── register/register.css
│   │   ├── home/home.css
│   │   ├── profile/profile.css
│   │   └── user_settings/settings.css
│   ├── js/
│   │   ├── login/login.js
│   │   ├── register/register.js
│   │   ├── home/home.js
│   │   ├── profile/profile.js
│   │   └── user_settings/settings.js
│   └── images/
│       ├── login/logo.svg
│       ├── register/logo.svg
│       ├── home/marker.svg
│       ├── profile/default-avatar.svg
│       └── user_settings/gear.svg
├── templates/
│   ├── base.html              # shared sidebar / shell / flash messages
│   ├── login/login.html
│   ├── register/register.html
│   ├── home/home.html
│   ├── profile/profile.html
│   └── user_settings/settings.html
└── config/                    # project settings (was evacu_project/)
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

Each app in `apps/` is registered in `INSTALLED_APPS` as `apps.<name>` (e.g. `apps.login`),
with an explicit `label` set in its `AppConfig` so the app label stays short (`login`,
`register`, `home`, `profile`, `user_settings`) for migrations, templates, and the ORM.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your Supabase DATABASE_URL
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

See `SUPABASE_SETUP.md` for connecting to a Supabase PostgreSQL database.

## Dark mode

Dark mode is a per-user preference stored on `UserSettings.dark_mode` (apps/user_settings).
`templates/base.html` renders the `dark-mode` class on `<body>` from
`user.settings.dark_mode`, and `static/css/base.css` defines the full set of light/dark
CSS variables consumed by every page's stylesheet — so the theme is consistent across
Home, Profile, and Settings, and persists across navigation (no client-side-only hacks).
