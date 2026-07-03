import streamlit as st

from core.config import settings


def render():
    """Render the about page."""
    st.title("ℹ️ About")

    content = f"""
## {settings.APP_TITLE}

**Version:** Sprint 5.1 - Dashboard Foundation  
**Status:** 🏗️ Foundation Complete  

### Architecture

```
Pages
  ↓
Services
  ↓
API Client
  ↓
FastAPI REST API
```

Layered frontend: pages handle UI, services handle logic, API client handles communication.

### Principles

- Separation of concerns  
- Reusable components  
- Clean API-only communication  
- Modular structure  
- Independent frontend  

### Stack

- Streamlit (Frontend)
- FastAPI (Backend)
- REST API communication
- PostgreSQL (via backend)
"""

    st.markdown(content)