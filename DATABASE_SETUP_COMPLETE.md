# Database Setup Complete

## Summary

The PostgreSQL database has been successfully installed, configured, and connected to the WealthFlow backend. All migrations have been applied and initial test data has been created.

## What Was Done

### 1. PostgreSQL Installation
- Installed PostgreSQL 16 on Ubuntu
- Service is running and enabled on boot
- Database cluster initialized at `/var/lib/postgresql/16/main`

### 2. Database Configuration
- **Database Name:** `wealthflow_prod`
- **Database User:** `flow_admin`
- **Database Password:** `wealthflow123`
- **Database Host:** `localhost`
- **Database Port:** `5432`

### 3. Database User Privileges
- Created user `flow_admin` with password `wealthflow123`
- Granted all privileges on database `wealthflow_prod`
- Granted all privileges on schema `public`
- Made user the owner of the database

### 4. Environment Configuration
Updated `backend/.env` with database credentials:
```env
DB_NAME=wealthflow_prod
DB_USER=flow_admin
DB_PASSWORD=wealthflow123
DB_HOST=localhost
DB_PORT=5432
```

### 5. Database Migrations
Successfully applied all migrations for:
- ✅ admin
- ✅ ai_copilot
- ✅ auth
- ✅ authentication
- ✅ bills
- ✅ budgeting
- ✅ contenttypes
- ✅ financial_calendar
- ✅ ledger
- ✅ payments
- ✅ receipts
- ✅ sessions
- ✅ token_blacklist

### 6. Initial Data Created

#### Admin User
- **Email:** admin@wealthflow.app
- **Password:** admin123
- **Role:** ADMIN

#### Test Account
- **Name:** Main Account
- **Type:** CHECKING
- **Balance:** $1,000.00
- **Currency:** USD

#### Test Categories
1. Food (EXPENSE)
2. Transportation (EXPENSE)
3. Shopping (EXPENSE)
4. Entertainment (EXPENSE)
5. Salary (INCOME)

#### Test Transactions
1. Grocery Shopping - $150.00 (Food)
2. Monthly Salary - $5,000.00 (Salary)
3. Gas Station - $50.00 (Transportation)

## How to Use

### Start the Backend Server
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

The backend will be available at: `http://192.168.1.68:8000`

### Test the API

#### 1. Login with Admin User
```bash
curl -X POST http://192.168.1.68:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@wealthflow.app",
    "password": "admin123"
  }'
```

Expected response:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "...",
    "email": "admin@wealthflow.app",
    "full_name": "Admin User",
    "avatar_url": null,
    "role": "ADMIN",
    "is_new_user": false
  }
}
```

#### 2. Get Transactions (with token)
```bash
curl http://192.168.1.68:8000/api/v1/ledger/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 3. Register a New User
```bash
curl -X POST http://192.168.1.68:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "name": "John Doe"
  }'
```

### Use the Android App

1. **Start the Android app** on your device/emulator
2. **Login** with the admin credentials:
   - Email: `admin@wealthflow.app`
   - Password: `admin123`
3. The app will automatically:
   - Authenticate with the backend
   - Load the test transactions
   - Sync data to the local database

## Database Management

### Connect to PostgreSQL
```bash
sudo -u postgres psql -d wealthflow_prod
```

### Useful Commands

#### View all tables
```sql
\dt
```

#### View users
```sql
SELECT email, full_name, role FROM users;
```

#### View transactions
```sql
SELECT t.title, t.amount, t.type, c.name as category 
FROM ledger_transaction t
JOIN ledger_category c ON t.category_id = c.id;
```

#### View accounts
```sql
SELECT name, balance, type FROM ledger_account;
```

### Backup Database
```bash
sudo -u postgres pg_dump wealthflow_prod > backup.sql
```

### Restore Database
```bash
sudo -u postgres psql -d wealthflow_prod < backup.sql
```

## Troubleshooting

### Backend won't start
- Ensure PostgreSQL is running: `sudo service postgresql status`
- Check database credentials in `backend/.env`
- Verify database exists: `sudo -u postgres psql -l`

### Can't connect from Android app
- Ensure phone and computer are on the same network
- Check firewall allows port 8000
- Verify backend is running on `0.0.0.0:8000` (not just `localhost:8000`)
- Test in browser: `http://192.168.1.68:8000/api/v1/auth/login/`

### Permission denied errors
```bash
# Re-grant permissions
sudo -u postgres psql -d wealthflow_prod -c "GRANT ALL ON SCHEMA public TO flow_admin;"
sudo -u postgres psql -d wealthflow_prod -c "GRANT ALL ON ALL TABLES TO flow_admin;"
```

## Next Steps

1. **Start the backend:**
   ```bash
   cd backend
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Run the Android app** and test login with `admin@wealthflow.app` / `admin123`

3. **Create additional users** via the registration screen in the app

4. **Add more test data** as needed for development

## Security Notes

⚠️ **Important:** This is a development setup. For production:

1. Change the database password in `.env`
2. Use a stronger `DJANGO_SECRET_KEY`
3. Enable `DEBUG=False`
4. Configure proper `ALLOWED_HOSTS`
5. Set up SSL/TLS certificates
6. Use environment variables for all secrets
7. Enable database connection pooling
8. Set up database backups

## Connection String

For reference, the database connection string is:
```
postgresql://flow_admin:wealthflow123@localhost:5432/wealthflow_prod
```

## Status

✅ PostgreSQL installed and running  
✅ Database created  
✅ User created with proper permissions  
✅ Environment configured  
✅ All migrations applied  
✅ Superuser created  
✅ Initial test data created  
✅ Backend ready to use  

**The database is fully connected and ready for use!**