#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error
set -o nounset  # Exit on unset variable
set -o pipefail # Exit on pipe failure

echo "========================================="
echo "🚀 Starting Render Deploy Build Process"
echo "========================================="

echo ""
echo "🔧 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "📦 Collecting static files..."
python manage.py collectstatic --no-input --clear

echo ""
echo "🔍 Checking database configuration..."
python manage.py check --database default --deploy

echo ""
echo "🗄️  Running database migrations..."
python manage.py migrate --no-input

echo ""
echo "👤 Creating superuser if needed..."
python manage.py criar_superuser

echo ""
echo "========================================="
echo "✅ Build completed successfully!"
echo "========================================="
