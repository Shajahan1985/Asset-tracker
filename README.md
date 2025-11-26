# Asset Tracker - Django Authentication System

## Project Setup

This Django project implements a comprehensive authentication and authorization system for a multi-user asset tracker application.

### Initial Setup Completed

1. **Django Project Created**: `asset_tracker`
2. **Authentication App Created**: `authentication`
3. **Database Initialized**: SQLite database with all migrations applied
4. **Superuser Created**: 
   - Username: `admin`
   - Password: `admin123`
   - Email: `admin@assettracker.com`

### Configuration

The following settings have been configured in `asset_tracker/settings.py`:

#### Authentication Settings
- Login URL: `/login/`
- Login redirect: `/dashboard/`
- Logout redirect: `/login/`

#### Session Settings
- Session timeout: 2 weeks (1,209,600 seconds)
- Session saved on every request
- Secure session cookies (HTTP-only, SameSite=Lax)

#### Email Backend
- Development: Console backend (emails printed to console)
- Password reset timeout: 1 hour

### Running the Project

```bash
# Run development server
python manage.py runserver

# Access admin interface
http://localhost:8000/admin/
```

### Next Steps

Refer to `.kiro/specs/django-auth-permissions/tasks.md` for the implementation plan.
