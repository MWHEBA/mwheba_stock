import os
import sys
import django
import sqlite3
from pathlib import Path

# Django superuser settings
DJANGO_SUPERUSER_USERNAME = 'admin'
DJANGO_SUPERUSER_PASSWORD = 'admin123'
DJANGO_SUPERUSER_EMAIL = 'admin@mwheba.com'

def create_database():
    """Create SQLite database if it doesn't exist"""
    try:
        # Get the base directory
        BASE_DIR = Path(__file__).resolve().parent
        db_path = BASE_DIR / 'db.sqlite3'
        
        # Check if database exists
        if db_path.exists():
            print(f"Database already exists at {db_path}")
        else:
            print(f"SQLite database will be created automatically during migrations")
        
        return True
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

def setup_django():
    """Set up Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

def run_migrations():
    """Run Django migrations"""
    try:
        print("Running migrations...")
        os.system('python manage.py makemigrations')
        os.system('python manage.py migrate')
        print("Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

def create_superuser():
    """Create Django superuser"""
    from django.contrib.auth.models import User
    
    try:
        if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
            print(f"Creating superuser '{DJANGO_SUPERUSER_USERNAME}'...")
            User.objects.create_superuser(
                username=DJANGO_SUPERUSER_USERNAME,
                email=DJANGO_SUPERUSER_EMAIL,
                password=DJANGO_SUPERUSER_PASSWORD
            )
            print(f"Superuser '{DJANGO_SUPERUSER_USERNAME}' created successfully!")
        else:
            print(f"Superuser '{DJANGO_SUPERUSER_USERNAME}' already exists.")
        return True
    except Exception as e:
        print(f"Error creating superuser: {e}")
        return False

def create_initial_data():
    """Create initial data for the application"""
    from inventory.models import (
        Category, StorageLocation, ExpenseCategory, CompanyProfile
    )
    
    try:
        # Create default categories
        if Category.objects.count() == 0:
            print("Creating default categories...")
            categories = [
                "إلكترونيات",
                "أجهزة منزلية",
                "أثاث",
                "ملابس",
                "أدوات مكتبية",
                "أخرى"
            ]
            for name in categories:
                Category.objects.create(name=name)
            print(f"Created {len(categories)} default categories.")
        
        # Create default storage locations
        if StorageLocation.objects.count() == 0:
            print("Creating default storage locations...")
            locations = [
                "المخزن الرئيسي",
                "المعرض",
                "مخزن البضائع الواردة"
            ]
            for name in locations:
                StorageLocation.objects.create(name=name)
            print(f"Created {len(locations)} default storage locations.")
        
        # Create default expense categories
        if ExpenseCategory.objects.count() == 0:
            print("Creating default expense categories...")
            expense_categories = [
                "إيجار",
                "رواتب",
                "مرافق",
                "نقل",
                "تسويق",
                "صيانة",
                "أخرى"
            ]
            for name in expense_categories:
                ExpenseCategory.objects.create(name=name)
            print(f"Created {len(expense_categories)} default expense categories.")
        
        # Create company profile
        if CompanyProfile.objects.count() == 0:
            print("Creating company profile...")
            CompanyProfile.objects.create(
                name="مخازن موهبة",
                address="القاهرة، مصر",
                phone="01234567890",
                email="info@mwheba.com",
                tax_number="123456789",
                registration_number="987654321"
            )
            print("Company profile created successfully!")
        
        return True
    except Exception as e:
        print(f"Error creating initial data: {e}")
        return False

def main():
    """Main function to set up the database and initial data"""
    print("Starting database setup...")
    
    # Create PostgreSQL database
    if not create_database():
        sys.exit(1)
    
    # Set up Django environment
    setup_django()
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    # Create superuser
    if not create_superuser():
        sys.exit(1)
    
    # Create initial data
    if not create_initial_data():
        sys.exit(1)
    
    print("\nSetup completed successfully!")
    print(f"You can now log in to the admin interface with:")
    print(f"Username: {DJANGO_SUPERUSER_USERNAME}")
    print(f"Password: {DJANGO_SUPERUSER_PASSWORD}")

if __name__ == "__main__":
    main()