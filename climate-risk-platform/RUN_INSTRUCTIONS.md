# 🚀 How to Run the Climate Risk Intelligence Platform

## Step 1: Start Docker Desktop

1. **Open Docker Desktop** from your Applications folder
2. **Wait for Docker to start** - you'll see a whale icon in your menu bar
3. **Verify Docker is running** by opening a terminal and running:
   ```bash
   docker info
   ```

## Step 2: Navigate to the Project

```bash
cd ~/FinHacks/climate-risk-platform
```

## Step 3: Start the Platform

### Option A: Use the Startup Script (Recommended)

```bash
./start.sh
```

This will automatically:
- Check if Docker is running
- Create environment file
- Start PostgreSQL and Redis
- Run database migrations
- Start backend API
- Start frontend

### Option B: Manual Start

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30

# Check status
docker-compose ps
```

## Step 4: Access the Platform

Once everything is running, open your browser:

- **🌐 Frontend Dashboard**: http://localhost:3000
- **🔧 Backend API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)

## Step 5: Test the Platform

### Quick Health Check

```bash
# Test backend
curl http://localhost:8000/health

# Get scenario templates
curl http://localhost:8000/api/scenarios/templates | jq

# Get sample portfolio
curl http://localhost:8000/api/portfolios/sample | jq
```

### Using the Dashboard

1. **Upload a Portfolio**
   - Click "Upload Portfolio" button
   - Use the sample CSV or create your own
   - Required fields: asset_id, asset_name, issuer_name, sector, country, latitude, longitude, market_value

2. **Select a Scenario**
   - Choose from 7 predefined scenarios:
     - Hurricane (coastal physical risk)
     - Wildfire (western US physical risk)
     - Drought (agricultural physical risk)
     - Heatwave (urban physical risk)
     - Flood (riverine physical risk)
     - Carbon Tax (transition risk)
     - Emissions Regulation (transition risk)

3. **Calculate Risk**
   - Click "Calculate Risk" button
   - Wait for analysis to complete (~10 seconds)
   - View results on the dashboard

4. **Explore Visualizations**
   - **Interactive Map**: Geographic risk distribution
   - **Portfolio Stats**: Key metrics (VaR, drawdown, hotspots)
   - **Loss Waterfall**: Sector contribution to losses
   - **Sector Heatmap**: Risk intensity by sector
   - **Issuer Table**: Sortable risk by issuer
   - **Recommendations**: Actionable suggestions

5. **Run MiroFish Cascade Simulation** (Optional)
   - Click "Run Cascade Analysis"
   - View dependency propagation
   - Read AI-generated narrative

6. **Export Report**
   - Click "Export Report" button
   - Download PDF executive summary

## Monitoring Services

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# PostgreSQL only
docker-compose logs -f postgres
```

### Check Service Status

```bash
docker-compose ps
```

Expected output:
```
NAME                      STATUS    PORTS
climate-risk-backend      Up        0.0.0.0:8000->8000/tcp
climate-risk-frontend     Up        0.0.0.0:3000->3000/tcp
climate-risk-postgres     Up        0.0.0.0:5432->5432/tcp
climate-risk-redis        Up        0.0.0.0:6379->6379/tcp
```

## Stopping the Platform

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Troubleshooting

### Docker Not Running
**Error**: `Cannot connect to the Docker daemon`

**Solution**: Start Docker Desktop and wait for it to fully start

### Port Already in Use
**Error**: `port is already allocated`

**Solution**: Stop other services using the ports:
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Find process using port 3000
lsof -ti:3000 | xargs kill -9
```

### Backend Not Starting
**Error**: Database connection failed

**Solution**: 
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check PostgreSQL logs
docker-compose logs postgres
```

### Frontend Not Loading
**Error**: Cannot connect to backend

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Restart frontend
docker-compose restart frontend
```

### Database Migration Issues
**Error**: Migration failed

**Solution**:
```bash
# Run migrations manually
docker-compose exec backend alembic upgrade head

# Or reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose exec backend alembic upgrade head
```

## Performance Expectations

- **Portfolio Upload** (< 1000 holdings): < 5 seconds
- **Risk Calculation** (< 1000 holdings): < 10 seconds
- **Dashboard Render**: < 3 seconds
- **Scenario Switch**: < 3 seconds
- **Map Update**: < 2 seconds
- **Report Generation**: < 10 seconds

## Sample Data

The platform includes sample portfolio data with:
- 100 diverse holdings
- Multiple sectors (Energy, Utilities, Real Estate, Manufacturing, etc.)
- Geographic distribution across US
- Varying risk profiles

Access via:
```bash
curl http://localhost:8000/api/portfolios/sample
```

## Next Steps

1. ✅ Start Docker Desktop
2. ✅ Run `./start.sh` or `docker-compose up -d`
3. ✅ Open http://localhost:3000
4. ✅ Upload a portfolio or use sample data
5. ✅ Select a scenario
6. ✅ Calculate risk
7. ✅ Explore visualizations
8. ✅ Export report

## Additional Resources

- **Verification Report**: `E2E_VERIFICATION_REPORT.md` - Detailed implementation status
- **Quick Start**: `QUICKSTART.md` - Alternative setup methods
- **Requirements**: `.kiro/specs/climate-risk-platform/requirements.md`
- **Design**: `.kiro/specs/climate-risk-platform/design.md`
- **Tasks**: `.kiro/specs/climate-risk-platform/tasks.md`

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`
3. Review test results: `backend/TEST_RESULTS.md`
4. Check verification report: `E2E_VERIFICATION_REPORT.md`

---

**Ready to explore climate risk intelligence!** 🌍📊
