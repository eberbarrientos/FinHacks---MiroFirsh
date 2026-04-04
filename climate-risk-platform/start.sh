#!/bin/bash

echo "🌍 Climate Risk Intelligence Platform - Startup Script"
echo "======================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo ""
    echo "On macOS:"
    echo "  1. Open Docker Desktop from Applications"
    echo "  2. Wait for Docker to start (whale icon in menu bar)"
    echo "  3. Run this script again"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
fi

# Start services
echo "🚀 Starting services..."
echo ""
docker-compose up -d postgres redis

echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if postgres is healthy
until docker exec climate-risk-postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready"
echo ""

# Run database migrations
echo "🔄 Running database migrations..."
cd backend
docker-compose run --rm backend alembic upgrade head 2>/dev/null || {
    echo "   Running migrations locally..."
    python3 -m alembic upgrade head
}
cd ..

echo "✅ Database migrations complete"
echo ""

# Start backend
echo "🚀 Starting backend API..."
docker-compose up -d backend

echo "⏳ Waiting for backend to be ready..."
sleep 5

# Check if backend is healthy
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    echo "   Waiting for backend..."
    sleep 2
done

echo "✅ Backend API is ready"
echo ""

# Start frontend
echo "🚀 Starting frontend..."
docker-compose up -d frontend

echo "⏳ Waiting for frontend to be ready..."
sleep 10

echo ""
echo "======================================================"
echo "✅ Climate Risk Intelligence Platform is running!"
echo "======================================================"
echo ""
echo "🌐 Frontend Dashboard:  http://localhost:3000"
echo "🔧 Backend API:         http://localhost:8000"
echo "📚 API Documentation:   http://localhost:8000/docs"
echo ""
echo "📊 Quick Test Commands:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/api/scenarios/templates"
echo ""
echo "🛑 To stop all services:"
echo "  docker-compose down"
echo ""
echo "📖 For more information, see QUICKSTART.md"
echo ""
