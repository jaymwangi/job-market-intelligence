class BaseService:
    """
    Base service class that all services inherit from.
    
    Provides:
    - API client injection
    - Common utility methods
    - Consistent service interface
    """
    
    def __init__(self, api_client):
        self.api = api_client  # Consistent attribute name