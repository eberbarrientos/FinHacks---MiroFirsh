# Climate Risk Intelligence Platform

A full-stack financial analysis system that enables institutions to assess, quantify, and visualize climate-related risks across investment portfolios.

## Features

- **Portfolio Risk Assessment**: Compute physical and transition risk scores
- **Scenario Stress Testing**: Apply climate scenarios to evaluate portfolio resilience
- **Financial Loss Estimation**: Calculate expected losses and climate VaR
- **Dependency Cascade Simulation**: Leverage MiroFish for systemic risk analysis
- **Interactive Visualization**: Maps, charts, and dashboards with premium UX
- **Recommendation Generation**: Actionable portfolio optimization suggestions

## Technology Stack

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL 15+
- Redis
- SQLAlchemy ORM
- Pydantic for validation

### Frontend
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Zustand for state management
- Mapbox GL for geospatial visualization

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start with Docker

1. Clone the repository
2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
3. Start all services:
   ```bash
   docker-compose up
   ```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database Setup

Run migrations:
```bash
cd backend
alembic upgrade head
```

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

## Project Structure

```
climate-risk-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── engines/      # Risk calculation engines
│   │   ├── adapters/     # External service adapters
│   │   └── utils/        # Utility functions
│   ├── alembic/          # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   ├── lib/              # Utility functions
│   └── store/            # State management
└── docker-compose.yml
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## License

Proprietary - All rights reserved
