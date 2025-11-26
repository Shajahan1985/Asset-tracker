"""
Script to create a superuser for initial admin access.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asset_tracker.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@assettracker.com',
        password='admin123'
    )
    print("Superuser 'admin' created successfully!")
    print("Username: admin")
    print("Password: admin123")
else:
    print("Superuser 'admin' already exists.")
