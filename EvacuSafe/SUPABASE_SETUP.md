# Supabase Setup — EvacuSafe

## 1. Create the Supabase project
1. Go to https://supabase.com/dashboard → **New Project**.
2. Pick a name, database password (save it), and region.
3. Wait for provisioning to finish.

## 2. Get your connection string
Project → **Settings → Database → Connection string → URI**.
Use the **Session pooler** or **Transaction pooler** string for hosted apps, or the
direct connection (port 5432) for local development:

```
postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

## 3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and paste your real connection string into `DATABASE_URL`, and set a
proper `SECRET_KEY` (any long random string).

## 4. Install dependencies
```bash
pip install -r requirements.txt
```
(This installs `psycopg2-binary` for the Postgres driver, `python-decouple` to read
`.env`, and `dj-database-url` to parse `DATABASE_URL` in `settings.py`.)

## 5. Verify the connection
```bash
python manage.py check
```
`settings.py` reads `DATABASE_URL` from `.env` — if it's set, Django connects to
Supabase Postgres; if it's blank, it falls back to local SQLite.

## 6. Create & apply migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
This creates all Django tables (`auth_user`, `dashboard_evacuationcenter`,
`profiles_profile`, `user_settings_usersettings`, etc.) in your Supabase Postgres
database, and seeds 5 sample evacuation centers via a data migration.

## 7. Create an admin user
```bash
python manage.py createsuperuser
```

## 8. Verify data in Supabase
Supabase Dashboard → **Table Editor** → select your project's tables (e.g.
`dashboard_evacuationcenter`, `auth_user`, `profiles_profile`,
`user_settings_usersettings`) and confirm rows are present. Registering a user
through `/register/` and editing their Profile/Settings should show up here live.

## 9. Run the app
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000/register/ to create an account, then explore
Home, Profile, and Settings.
