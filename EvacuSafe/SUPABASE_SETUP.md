# Supabase Setup — EvacuSafe

## 1. Create the Supabase project
1. Go to https://supabase.com/dashboard → **New Project**.
2. Pick a name, database password (save it securely), and select your desired region.
3. Wait for project provisioning to complete.

## 2. Get your connection string
In your Supabase project dashboard:
Navigate to **Project Settings → Database → Connection string → URI**.

Choose the appropriate connection URI:
- **Transaction Pooler (port 6543):** Recommended for containerized or serverless deployments (Render, Railway, Heroku).
- **Session Pooler (port 5432):** Alternative pooler mode.
- **Direct Connection (port 5432):** Recommended for migrations and local development if direct external IPv4/IPv6 access is supported.

Connection string format:
```text
postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

## 3. Configure environment variables
Copy the environment template:
```bash
cp .env.example .env
```
Edit `.env` and set:
- `DATABASE_URL`: Your Supabase PostgreSQL URI (with `sslmode=require`).
- `SECRET_KEY`: A cryptographically secure random string.
- `DEBUG`: `False` for production (`True` for local development).
- `SUPABASE_URL` and `SUPABASE_ANON_KEY`: From **Project Settings → API**.

## 4. Install dependencies
```bash
pip install -r requirements.txt
```
This installs `psycopg2-binary` (PostgreSQL driver), `python-decouple` (environment parser), `dj-database-url` (connection string parser), `whitenoise` (static file serving), and `gunicorn` (production WSGI server).

## 5. Verify the connection & system health
```bash
python manage.py check
```
`settings.py` reads `DATABASE_URL` from `.env`. When running automated tests (`python manage.py test`), Django automatically isolates runs by using in-memory SQLite so test executions never hit or wipe your production Supabase database.

## 6. Apply database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
This applies all migrations and provisions tables in Supabase:
- `auth_user` (Django authentication)
- `home_evacuationcenter` (Evacuation centers, locations, and capacities)
- `home_auditlog` (Complete audit trail of center and status updates)
- `home_incident` (Active disaster incidents and alert levels)
- `home_resourceinventory` (Relief supplies: food, water, medical kits, blankets)
- `profile_profile` (User profiles, avatars, responder contact info, and roles)
- `user_settings_usersettings` (Notifications, language, and theme preferences)

## 7. Create an admin user
```bash
python manage.py createsuperuser
```

## 8. Verify tables in Supabase Table Editor
1. In the Supabase Dashboard, navigate to **Table Editor**.
2. Confirm the core tables are present: `home_evacuationcenter`, `auth_user`, `profile_profile`, `user_settings_usersettings`, `home_auditlog`, `home_incident`, `home_resourceinventory`.
3. Newly registered users and center status changes will be persisted directly to Supabase.

## 9. Run the application
```bash
# Local development server
python manage.py runserver

# Or production WSGI server
gunicorn config.wsgi:application
```
Visit http://127.0.0.1:8000/ to access EvacuSafe.
