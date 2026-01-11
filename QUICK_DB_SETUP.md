# Quick Setup Guide - Cloud Database

Since Docker and PostgreSQL are not installed on your system, the easiest way to get started is with a **free cloud database**.

## Recommended: Render.com (Free Tier)

### Step 1: Create Free PostgreSQL Database

1. Go to **[render.com](https://render.com)** and sign up (free)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `infragen-db`
   - **Database:** `infragen_db`
   - **User:** `infragen_user`
   - **Region:** Choose closest to you
   - **PostgreSQL Version:** 15 or later
   - **Plan:** **Free** (select this!)
4. Click **"Create Database"**
5. Wait 1-2 minutes for provisioning

### Step 2: Copy Connection String

On the database page, look for **"External Database URL"**:
```
postgres://username:password@host:5432/database_name
```

Copy this **entire URL**.

### Step 3: Update `.env` File

The `.env` file has been created for you in the project root with a placeholder.

**Open the `.env` file** and replace the `DATABASE_URL` with your Render URL:

```bash
# Replace this line with your Render database URL
DATABASE_URL=postgresql://your_render_url_here
```

### Step 4: Test Connection

```bash
python test_database_integration.py
```

You should see:
```
✅ Database connection successful
✅ Database tables created successfully
✅ All tests passed!
```

### Step 5: Start Backend

```bash
uvicorn backend.main:app --reload
```

---

## Alternative: Supabase (Also Free)

1. Go to **[supabase.com](https://supabase.com)** and sign up
2. Create new project
3. Go to **Settings → Database**
4. Find **Connection String** (URI mode)
5. Copy the URL and update `.env`

---

## Alternative: ElephantSQL (Also Free)

1. Go to **[elephantsql.com](https://www.elephantsql.com/)**
2. Sign up and create "Tiny Turtle" free instance
3. Copy the **URL**
4. Update `.env` with this URL

---

## I've Already Created

✅ **`.env` file** in project root (with placeholder)
✅ **All database code** is ready and tested
✅ **Test script** to verify connection

## What You Need to Do

1. Sign up for Render (or Supabase/ElephantSQL)
2. Create free PostgreSQL database
3. Copy the connection URL
4. Edit `.env` file with your URL
5. Run test: `python test_database_integration.py`
6. Start backend: `uvicorn backend.main:app --reload`

**Total time: ~5 minutes** ⏱️

Need help? See `DATABASE_SETUP.md` for detailed instructions!
