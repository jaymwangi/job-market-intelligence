# scripts/test_settings.py
from config import settings


def main():
    """Test the configuration system."""
    print("=" * 50)
    print("Configuration Test")
    print("=" * 50)
    print(f"Application: {settings.app_name}")
    print(f"Environment: {settings.environment}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    print(f"Database URL: {settings.database_url}")
    print("=" * 50)
    print("✅ Configuration loaded successfully!")


if __name__ == "__main__":
    main()
