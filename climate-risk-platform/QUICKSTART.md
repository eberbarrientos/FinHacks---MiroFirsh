# Climate Risk Intelligence Platform - Quick Start Guide

## Prerequisites

✅ Python 3.9.6 (Detected)
✅ Node.js v25.6.1 (Detected)

## Option 1: Run with Docker (Recommended)

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your Mac.

### Step 2: Start Services
```bash
cd climate-risk-platform
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Frontend (port 3000)
- MiroFish Backend (port 8080)

### Step 3: Access the Application
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Option 2: Run Locally (Without Docker)

### Step 1: Install PostgreSQL and Redis

**Using Homebrew:**
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

### Step 2: Create Database
```bash
createdb climate_risk
```

### Step 3: Set Up Backend

```bash
cd climate-risk-platform/backend

# Install dependencies
pip3 install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### Step 4: Set Up Frontend (New Terminal)

```bash
cd climate-risk-platform/frontend

# Dependencies are already installed
# Start the development server
npm run dev
```

Frontend will be available at: http://localhost:3000

---

## Option 3: Demo Mode (Backend Only - No Database)

If you just want to explore the API and test the risk engines:

```bash
cd climate-risk-platform/backend

# Run the test suite (uses in-memory SQLite)
python3 -m pytest tests/ -v

# View test results
cat TEST_RESULTS.md
```

This will run all 141 tests and show you the platform's capabilities.

---

## Quick Test

Once the backend is running, test it:

```bash
# Check health
curl http://localhost:8000/health

# Get scenario templates
curl http://localhost:8000/api/scenarios/templates

# Get sample portfolio data
curl http://localhost:8000/api/portfolios/sample
```

---

## What to Try First

1. **Upload a Portfolio**: Use the sample CSV or create your own
2. **Select a Scenario**: Choose from 7 predefined climate scenarios
3. **Calculate Risk**: Click "Calculate Risk" to run the analysis
4. **Explore the Map**: View geographic risk distribution
5. **Review Recommendations**: See actionable portfolio optimization suggestions
6. **Export Report**: Generate a PDF executive summary

---

## Troubleshooting

### Docker Issues
- **"Cannot connect to Docker daemon"**: Start Docker Desktop
- **Port already in use**: Stop other services using ports 3000, 5432, 6379, 8000, 8080

### Backend Issues
- **Database connection error**: Make sure PostgreSQL is running
- **Redis connection error**: Make sure Redis is running
- **Import errors**: Run `pip3 install -r requirements.txt`

### Frontend Issues
- **Module not found**: Run `npm install` in the frontend directory
- **API connection error**: Make sure backend is running on port 8000

---

## Next Steps

- Review the [E2E Verification Report](E2E_VERIFICATION_REPORT.md) for detailed implementation status
- Check the [Requirements Document](.kiro/specs/climate-risk-platform/requirements.md)
- Explore the [Design Document](.kiro/specs/climate-risk-platform/design.md)
- View the [Implementation Tasks](.kiro/specs/climate-risk-platform/tasks.md)

---

## Performance Targets

- Portfolio upload (< 1000 holdings): **< 5 seconds**
- Risk calculation (< 1000 holdings): **< 10 seconds**
- Dashboard render: **< 3 seconds**
- Scenario switch: **< 3 seconds**

---

## Support

For issues or questions, refer to:
- Backend logs: Check terminal output
- Frontend logs: Check browser console (F12)
- Test results: `climate-risk-platform/backend/TEST_RESULTS.md`
- Verification report: `climate-risk-platform/E2E_VERIFICATION_REPORT.md`
