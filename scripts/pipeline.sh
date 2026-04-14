#!/bin/sh
set -e  # stop immédiatement si erreur

echo "🔹 Installing dependencies..."
apk add --no-cache python3 py3-pip curl

echo "🔹 Installing Python tools..."
pip install --break-system-packages pytest pip-audit

echo "🔹 Running tests..."
pytest || exit 1

echo "🔹 Auditing dependencies..."
pip-audit || exit 1

echo "🔹 Installing Trivy..."
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

echo "🔹 Building Docker image..."
docker build -t test-app . || exit 1

echo "🔹 Scanning Docker image..."
./bin/trivy image --exit-code 1 --severity HIGH,CRITICAL test-app

echo "✅ Pipeline finished successfully"