#!/bin/sh
set -e

echo "🔹 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip curl docker.io

echo "🔹 Installing Python tools..."
pip3 install pytest pip-audit

echo "🔹 Running tests..."
pytest

echo "🔹 Auditing dependencies..."
pip-audit

echo "🔹 Building Docker image..."
docker build -t myapp .

echo "🔹 Installing Trivy"
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

echo "🔹 Scanning Docker image..." 
./bin/trivy image --exit-code 1 --severity HIGH,CRITICAL myapp

echo "✅ Pipeline finished successfully"
