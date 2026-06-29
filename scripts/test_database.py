# scripts/test_database.py
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.health import check_database_connection, get_database_status
from app.database.session import engine
from config import settings
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def test_connection_details() -> None:
    """Test database connection with detailed error reporting."""
    print("=" * 60)
    print("Database Connection Test - Detailed")
    print("=" * 60)
    
    # Show connection info (mask password for security)
    masked_url = settings.database_url.replace(settings.database_password, "***")
    print(f"Connection URL: {masked_url}")
    print("-" * 60)
    
    # Test connection
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Connection successful!")
            print(f"   Result: {result.scalar()}")
            
            # Get PostgreSQL version
            result = connection.execute(text("SELECT version()"))
            version: Optional[str] = result.scalar()
            if version:
                print(f"   PostgreSQL version: {version.split(',')[0]}")
            else:
                print("   PostgreSQL version: unknown")
            
            # Get current database
            result = connection.execute(text("SELECT current_database()"))
            db_name: Optional[str] = result.scalar()
            if db_name:
                print(f"   Connected to database: {db_name}")
            else:
                print("   Connected to database: unknown")
            
    except OperationalError as e:
        print("❌ Connection failed!")
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Is PostgreSQL running?")
        print("   sudo systemctl status postgresql  # Linux")
        print("   brew services list                 # macOS")
        print("   Get-Service postgresql             # Windows")
        
        print("\n2. Does the database exist?")
        print(f"   createdb -U {settings.database_user} {settings.database_name}")
        
        print("\n3. Are credentials correct?")
        print(f"   User: {settings.database_user}")
        print(f"   Password: {'*' * len(settings.database_password)} (check .env)")
        
        print("\n4. Test connection manually:")
        print(f"   psql -U {settings.database_user} -h {settings.database_host} -p {settings.database_port} -d postgres")
        
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=" * 60)


def main() -> None:
    """Main test function."""
    test_connection_details()


if __name__ == "__main__":
    main()