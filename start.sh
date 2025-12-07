#!/bin/bash

# Qubic Risk Radar - One Command Startup Script
# This script sets up and runs the entire application with a single command

set -e

echo "🚀 Qubic Risk Radar - Starting..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your configuration."
    echo ""
    echo "📝 Required environment variables:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - JWT_SECRET"
    echo "   - GEMINI_API_KEY"
    echo ""
    read -p "Press Enter after editing .env file to continue..."
fi

echo "🔧 Building and starting services..."
echo ""

# Build and start all services
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

echo ""
echo "✅ Application is ready!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Services running:"
docker-compose ps
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
