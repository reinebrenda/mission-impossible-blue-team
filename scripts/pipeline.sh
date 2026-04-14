#!/bin/sh
set -e

echo "🔹 Installing dependencies..."
apk add --no-cache python3 py3-pip
pip install pytest requests

echo "🔹 Running tests..."
pytest || exit 1

echo "🔹 Checking dependencies..."
pip install pip-audit
pip-audit || exit 1

echo "🔹 Building Docker image..."
docker build -t devsecops-app .

echo "🔹 Scanning Docker image..."
docker run --rm aquasec/trivy image --exit-code 1 --severity HIGH,CRITICAL devsecops-app

echo "✅ Pipeline sécurisé"