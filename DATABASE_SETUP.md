# PostgreSQL Database Setup Guide

This guide explains how to set up PostgreSQL for the AI-Driven Infrastructure Generator.

## Quick Start with Docker (Recommended)

The fastest way to get PostgreSQL running locally:

```bash
docker run --name infragen-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=infragen_db \
  -p 5432:5432 \
  -d postgres:15
```

Then create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/infragen_db
```

## Local PostgreSQL Installation

### Windows

1. **Download PostgreSQL**: Visit [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. **Run Installer**: Install PostgreSQL 15 or later
3. **Set Password**: Remember the password you set for the `postgres` user
4. **Create Database**:
   ```powershell
   # Open Command Prompt and run:
   psql -U postgres
   CREATE DATABASE infragen_db;
   \q
   ```

### macOS

```bash
# Install via Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb infragen_db
```

### Linux (Ubuntu/Debian)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb infragen_db
```

## Cloud Database Options

### Option 1: Render (Free Tier Available)

1. Go to [render.com](https://render.com)
2. Create a new PostgreSQL database
3. Copy the **External Database URL**
4. Add to `.env`:
   ```
   DATABASE_URL=your_external_url_from_render
   ```

### Option 2: Supabase (Free Tier Available)

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **Settings → Database**
4. Copy the **Connection String** (URI format)
5. Add to `.env`:
   ```
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres
   ```

### Option 3: Railway (Free Trial)

1. Go to [railway.app](https://railway.app)
2. Create a new PostgreSQL database
3. Copy the **Connection URL**
4. Add to `.env`

### Option 4: ElephantSQL (Free Tier Available)

1. Go to [elephantsql.com](https://www.elephantsql.com/)
2. Create a free "Tiny Turtle" instance
3. Copy the **URL**
4. Add to `.env`

## Environment Configuration

Create a `.env` file in the project root:

```bash
# Required: Database connection
DATABASE_URL=postgresql://username:password@host:port/database_name

# Optional: Development settings
SQL_ECHO=false          # Set to 'true' to see all SQL queries
SQL_DEBUG=false         # Set to 'true' to see connection events

# Optional: Google Gemini API
GOOGLE_API_KEY=your_api_key_here
```

### Connection String Format

```
postgresql://[username]:[password]@[host]:[port]/[database_name]?[options]
```

**Examples:**

- Local: `postgresql://postgres:password@localhost:5432/infragen_db`
- Remote: `postgresql://user:pass@db.example.com:5432/mydb`
- With SSL: `postgresql://user:pass@host:5432/db?sslmode=require`

## Application Setup

### 1. Install Dependencies

```bash
cd c:\Users\Dell\Downloads\daiict-diya\daiict-diya\github-repo
pip install -r requirements.txt
```

### 2. Configure Database

Create `.env` file with your database connection string (see above).

### 3. Start the Application

```bash
# The database tables will be created automatically on first run
uvicorn backend.main:app --reload
```

You should see:
```
🚀 Starting AI-Driven Infrastructure Generator...
✅ Database connection successful
✅ Database tables created successfully
✅ Application ready!
```

## Verify Database Setup

### Option 1: Using psql

```bash
# Connect to database
psql -U postgres -d infragen_db

# List all tables
\dt

# You should see:
# infrastructure_models
# vpcs
# ec2_instances
# rds_databases
# load_balancers
# s3_buckets
# security_groups
# nat_gateways
# vpc_flow_logs

# Exit
\q
```

### Option 2: Using Docker

```bash
docker exec -it infragen-postgres psql -U postgres -d infragen_db -c "\dt"
```

### Option 3: Query from Python

```python
from backend.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables:", tables)
```

## Testing Persistence

1. **Generate Infrastructure**:
   ```bash
   curl -X POST http://localhost:8000/text \
     -H "Content-Type: application/json" \
     -d '{"text": "Create a VPC with an EC2 instance"}'
   ```

2. **Note the `model_id`** from the response

3. **Restart the Backend**:
   ```bash
   # Press Ctrl+C, then:
   uvicorn backend.main:app --reload
   ```

4. **Query the Database**:
   ```bash
   psql -U postgres -d infragen_db -c "SELECT model_id, created_at FROM infrastructure_models;"
   ```

5. **Verify Model Still Exists**: The model should persist after restart!

## Database Migrations (Advanced)

For production deployments, use Alembic for database migrations:

```bash
# Initialize Alembic (only once)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

## Troubleshooting

### Connection Refused

**Problem**: `could not connect to server: Connection refused`

**Solutions**:
- Ensure PostgreSQL is running: `pg_isready`
- Check if port 5432 is open: `netstat -an | find "5432"`
- Verify connection string format

### Authentication Failed

**Problem**: `password authentication failed for user`

**Solutions**:
- Double-check username and password in connection string
- Ensure special characters in password are URL-encoded
- For local PostgreSQL, check `pg_hba.conf` authentication settings

### Database Does Not Exist

**Problem**: `database "infragen_db" does not exist`

**Solution**:
```bash
createdb infragen_db
# OR
psql -U postgres -c "CREATE DATABASE infragen_db;"
```

### Tables Not Created

**Problem**: Tables are not being created automatically

**Solution**:
1. Check application startup logs for errors
2. Manually create tables:
   ```python
   from backend.database import init_db
   init_db()
   ```

### SSL Required (Cloud Databases)

**Problem**: Cloud provider requires SSL

**Solution**:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

## Production Recommendations

1. **Use Connection Pooling**: Already configured with SQLAlchemy (pool_size=10)
2. **Enable SSL**: Add `?sslmode=require` to production connection strings
3. **Use Environment Variables**: Never commit `.env` to version control
4. **Regular Backups**: Use `pg_dump` or cloud provider backup features
5. **Monitoring**: Monitor connection pool usage and query performance

## Backup and Restore

### Backup

```bash
# Full database backup
pg_dump -U postgres infragen_db > backup.sql

# Docker backup
docker exec infragen-postgres pg_dump -U postgres infragen_db > backup.sql
```

### Restore

```bash
# Restore from backup
psql -U postgres infragen_db < backup.sql

# Docker restore
docker exec -i infragen-postgres psql -U postgres infragen_db < backup.sql
```

## Need Help?

- **PostgreSQL Documentation**: [postgresql.org/docs](https://www.postgresql.org/docs/)
- **SQLAlchemy Documentation**: [docs.sqlalchemy.org](https://docs.sqlalchemy.org/)
- **FastAPI Database Guide**: [fastapi.tiangolo.com/tutorial/sql-databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
