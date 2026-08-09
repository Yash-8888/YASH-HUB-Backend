# Candy Hub — Backend (FastAPI)

Verified: app imports cleanly, all 30 routes register, and every SQLAlchemy
model compiles to valid Postgres DDL (checked with `CreateTable(...).compile()`
against the postgres dialect). You still need a real Postgres instance to run
end-to-end — the DDL check confirms the schema is correct but doesn't replace
that.

## 1. Install PostgreSQL locally (if you don't have it)

**Windows:** install from https://www.postgresql.org/download/windows/
**Mac:** `brew install postgresql@16 && brew services start postgresql@16`
**Linux (Ubuntu/Debian):** `sudo apt install postgresql postgresql-contrib`

## 2. Create the database + user

```bash
psql postgres
```
```sql
CREATE USER candyhub_user WITH PASSWORD 'candyhub_pass';
CREATE DATABASE candyhub OWNER candyhub_user;
\q
```

(Match these to whatever you put in `.env` — the defaults in `.env.example`
already use these values, so you can copy-paste as-is for local dev.)

## 3. Set up the Python environment

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` — at minimum, change `SECRET_KEY` to something random:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 4. Create the tables

```bash
python -m scripts.create_tables
```

This creates `users`, `giveaways`, `giveaway_entries`, `rewards`,
`user_rewards`, and `announcements` directly from the SQLAlchemy models.
Once the schema stabilizes you'll want to switch to Alembic migrations
instead of re-running this script — this is a fast path for local dev.

## 5. Create your admin account

Set `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` in `.env`, then:

```bash
python -m scripts.create_admin
```

## 6. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger docs — every
endpoint below is testable there without writing any frontend code yet.

## Endpoints implemented (Phase 1 core)

**Auth**
- `POST /api/auth/register` — email + password, optional `referred_by` code
- `POST /api/auth/login` — returns JWT bearer token

**Users**
- `GET /api/users/profile` — current user's full profile
- `PATCH /api/users/profile` — update roblox_username / discord_id
- `GET /api/leaderboard` — top members by points (public)

**Giveaways**
- `GET /api/giveaways` — list all (optional `?status_filter=active`)
- `GET /api/giveaways/{id}` — single giveaway
- `POST /api/giveaways/{id}/enter` — enter (requires roblox_username set)
- `POST /api/giveaways` — admin: create
- `PATCH /api/giveaways/{id}` — admin: update
- `DELETE /api/giveaways/{id}` — admin: delete
- `POST /api/giveaways/{id}/pick-winners` — admin: random winner selection

**Rewards**
- `GET /api/rewards` — list rewards catalog
- `POST /api/rewards/{id}/redeem` — spend points on a reward
- `POST /api/rewards` — admin: create
- `DELETE /api/rewards/{id}` — admin: delete

**Announcements**
- `GET /api/announcements` — list (pinned first)
- `POST /api/announcements` — admin: create
- `DELETE /api/announcements/{id}` — admin: delete
- `PATCH /api/announcements/{id}/pin` — admin: toggle pin

**Admin — user management**
- `GET /api/admin/users?q=` — search by email or roblox username
- `POST /api/admin/users/ban` — ban/unban
- `POST /api/admin/users/points` — add/remove points
- `POST /api/admin/users/reset-entries` — clear a user's giveaway entries

## Auth in Swagger UI

Click "Authorize" in `/docs`, register a user via `/api/auth/register` first
(it returns a token directly), or log in and paste the `access_token` value.

## What's deliberately deferred to later phases

- Discord OAuth / Roblox account verification (Phase 4) — `discord_id` and
  `roblox_username` are plain text fields for now, filled in manually
- Redis / Celery (marked "future" in your spec) — not wired in yet, nothing
  here depends on them
- Alembic migration files — the models are ready for `alembic revision
  --autogenerate` whenever you want to switch off `create_tables.py`
- Referral tracking is a simple points bump on registration; there's no
  `referrals` table yet to show "who invited who" in the admin panel
