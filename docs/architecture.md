
# Job Market Intelligence

## Architecture Document

### Version
v1.0

---

# 1. Architecture Overview

Job Market Intelligence is a full-stack job market analytics platform with a clean layered architecture.

## System Components


┌─────────────────────────────────────────────────────────────────┐
│                    External Data Sources                        │
│              (Adzuna, Indeed, LinkedIn APIs)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ETL Pipeline                               │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐              │
│  │  Extract  │ →  │ Transform │ →  │   Load    │              │
│  └───────────┘    └───────────┘    └───────────┘              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                          │
│              (Jobs, Skills, Analytics Data)                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Repository Layer                             │
│              (Data Access Abstraction)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer                                │
│              (Business Logic, Analytics)                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                             │
│              (HTTP Endpoints, Validation)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Streamlit Dashboard                           │
│              (Data Visualization, UI)                           │
└─────────────────────────────────────────────────────────────────┘
```

## Why Layered Architecture?

| Benefit | Description |
|---------|-------------|
| **Maintainability** | Each layer can be modified independently |
| **Testability** | Layers can be tested in isolation |
| **Scalability** | Components can be scaled independently |
| **Reliability** | Failure in one layer doesn't cascade |
| **Clarity** | Each layer has a single responsibility |

---

# 2. Dashboard Architecture

## Overview

The Streamlit dashboard follows a clean layered architecture with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Pages Layer                             │
│              (UI Orchestration Only)                            │
│                                                                 │
│  • Only call services                                           │
│  • Render components                                            │
│  • No HTTP requests                                             │
│  • No business logic                                            │
│  • No data transformation                                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                            │
│              (Business Logic + Anti-Corruption)                 │
│                                                                 │
│  • Call API endpoints                                           │
│  • Validate responses                                           │
│  • Normalize DTOs → Domain Models                               │
│  • Apply business rules                                         │
│  • Coordinate caching                                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Mapper Layer                             │
│              (Presentation Transformation)                      │
│                                                                 │
│  • Domain Models → Chart Models                                 │
│  • Prepare visualization-ready data                             │
│  • Shield charts from business changes                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Chart Components                           │
│              (Pure Plotly Figures)                              │
│                                                                 │
│  • Accept chart models                                          │
│  • Return Plotly figures                                        │
│  • No business logic                                            │
│  • No API calls                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Example

```python
# 1. Page calls service
chart_data = service.get_skills_chart()

# 2. Service fetches from API
data = self.api_client.get('/api/v1/analytics/top-skills')

# 3. Service normalizes to domain models
skills = [TopSkill(**item) for item in data]

# 4. Service uses mapper to transform
chart = self.mapper.to_horizontal_bar_chart(skills)

# 5. Page receives presentation-ready data
fig = create_horizontal_bar_chart(chart_data)

# 6. Dashboard renders chart
st.plotly_chart(fig)
```

## Layer Rules

| Layer | Can Do | Cannot Do |
|-------|--------|-----------|
| **Pages** | UI orchestration, render components | HTTP, Plotly, business logic, transformations |
| **Services** | API calls, validation, normalization | Streamlit, session state, visualization |
| **Mappers** | Domain → Chart Model transformation | HTTP, UI, business logic |
| **Charts** | Plotly figure creation | API calls, backend knowledge, business logic |
| **API Client** | HTTP transport | Business logic, caching, visualization |

---

# 3. Dashboard Components

## Component Structure

```
dashboard/components/
├── alerts.py         # Accessible alert messages (error, success, warning, info)
├── charts.py         # Reusable Plotly chart library (bar, line, pie, donut, histogram)
├── empty_state.py    # Empty states with suggestions and reset options
├── filters.py        # Job filter UI components
├── icons.py          # Professional SVG icon system
├── layout.py         # Reusable layout components (headers, dividers, stats bars)
├── loading.py        # Loading states (spinners, skeleton loaders)
├── metrics.py        # KPI metric cards with professional styling
├── pagination.py     # Pagination controls
├── sidebar.py        # Professional navigation sidebar
└── tables.py         # Job tables with inline expansion
```

## Component Responsibilities

### `icons.py`
Central SVG icon system for professional look.

```python
# Usage
icon = get_icon("analytics", size=24, color="#1a1a2e")
st.markdown(f'<span>{icon}</span>', unsafe_allow_html=True)
```

### `charts.py`
Pure Plotly figure factory.

```python
# Each function accepts a chart model and returns a Plotly figure
create_bar_chart(data: BarChartData) -> go.Figure
create_line_chart(data: LineChartData) -> go.Figure
create_pie_chart(data: PieChartData) -> go.Figure
```

### `metrics.py`
Professional KPI metric cards.

```python
# Renders a metric card with SVG icon
render_metric_card(metric: MetricCardData)
```

### `layout.py`
Consistent page layout components.

```python
page_header(title, subtitle, icon)  # Page header with SVG icon
section_header(title, subtitle, icon)  # Section header
divider()  # Visual divider
stats_bar(stats)  # Stats bar with SVG icons
```

---

# 4. Dashboard Pages

## Page Structure

```
dashboard/pages/
├── overview.py      # Dashboard overview with KPI cards and recent jobs
├── jobs.py          # Job explorer with search, filters, and pagination
├── analytics.py     # Full analytics dashboard (skills, companies, locations, salary, trends)
└── about.py         # Project information
```

## Page Responsibilities

| Page | Purpose | Key Features |
|------|---------|--------------|
| **Overview** | Dashboard summary | KPI cards, recent jobs, quick navigation, API status |
| **Jobs** | Job search and browsing | Filters, search, pagination, job details expansion |
| **Analytics** | Market insights | Skills, companies, locations, salary, employment types, trends |
| **About** | Project information | Architecture overview, tech stack, principles |

---

# 5. Caching Strategy

## Per-Endpoint TTLs

| Endpoint | TTL | Purpose |
|----------|-----|---------|
| Dashboard Summary | 5 min | Quick overview data |
| Top Skills | 10 min | Skills demand trends |
| Top Companies | 10 min | Company hiring trends |
| Jobs by Location | 10 min | Geographic distribution |
| Salary Statistics | 15 min | Stable salary data |
| Salary Distribution | 15 min | Stable salary distribution |
| Employment Types | 10 min | Employment trends |
| Posting Trend | 5 min | Real-time trends |

## Cache Implementation

```python
@cached(ttl=300)  # 5 minutes
def get_dashboard_metrics(self):
    # Expensive API call
    return self._fetch_dashboard_summary()
```

## Manual Refresh

All pages include a refresh button that:
1. Clears all caches
2. Reloads data from API
3. Re-renders visualizations

---

# 6. Testing Strategy

## Test Structure

```
dashboard/tests/
├── test_analytics_mapper.py  # Mapper transformations (9 tests)
├── test_analytics_service.py # Service API calls (16 tests)
└── test_charts.py            # Chart generation (13 tests)
```

## Running Tests

```bash
# Run all dashboard tests
python -m pytest dashboard/tests/ -v

# Run specific test file
python -m pytest dashboard/tests/test_analytics_mapper.py -v
```

## Test Coverage

| Layer | Tests | What's Tested |
|-------|-------|---------------|
| Mapper | 9 | Domain → Chart Model transformations |
| Service | 16 | API calls, validation, error handling, caching |
| Charts | 13 | Plotly figure generation with various data states |

---

# 7. Development Workflow

## Setup

```bash
# Clone repository
git clone <repository-url>
cd job-market-analytics-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend
uvicorn app.main:app --reload

# Run Streamlit dashboard (in new terminal)
streamlit run dashboard/app.py
```

## Environment Variables

```bash
# .env file
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30
CACHE_TTL_DEFAULT=300
ENABLE_CACHE=True
APP_TITLE=Job Market Dashboard
APP_ICON=📊
DEBUG=False
```

## Quality Checks

```bash
# Linting
ruff check dashboard/

# Formatting
black dashboard/

# Type checking
mypy dashboard/ --explicit-package-bases --ignore-missing-imports

# Run all quality checks
ruff check dashboard/ && black dashboard/ && mypy dashboard/ --explicit-package-bases --ignore-missing-imports
```

---

# 8. Sprint Timeline

| Sprint | Focus | Status |
|--------|-------|--------|
| 5.1 | Dashboard Foundation | ✅ Complete |
| 5.2 | Job Explorer | ✅ Complete |
| 5.3 | Analytics Dashboard | ✅ Complete |
| 5.4 | Polish & Production Readiness | ✅ Complete |

## Sprint 5.4 Deliverables

| Area | Deliverable | Status |
|------|-------------|--------|
| Performance | Per-endpoint caching, optimized API usage | ✅ |
| UX | Loading states, empty states, friendly errors | ✅ |
| UI | Professional SVG icons, consistent styling | ✅ |
| Code Quality | Ruff, Black, MyPy passing | ✅ |
| Testing | 38 tests passing | ✅ |
| Documentation | Architecture docs updated | ✅ |

---

# 9. Architecture Constraints

## Must Follow

- ✅ Remain modular with clear layer boundaries
- ✅ Use repository pattern for data access
- ✅ Use service layer pattern for business logic
- ✅ Pages must only orchestrate, never transform data
- ✅ Services must own the mapper
- ✅ Components must remain reusable
- ✅ Use SVG icons for professional appearance

## Must Avoid

- ❌ Business logic in routes
- ❌ Direct database access from dashboard
- ❌ Global mutable state
- ❌ Pages calling HTTP directly
- ❌ Pages using mapper directly
- ❌ Charts containing business logic

---

# 10. Definition of Done

A feature is complete when:

1. ✅ Code follows layered architecture
2. ✅ Tests pass
3. ✅ Ruff and Black checks pass
4. ✅ MyPy type checking passes
5. ✅ Documentation updated
6. ✅ No dead code or debug prints
7. ✅ Loading, empty, and error states implemented
8. ✅ Professional UI with SVG icons

---

End of Architecture Document
```