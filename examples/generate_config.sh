#!/bin/bash
# Example script: Generate service configuration from template
# This demonstrates how to use the config generate command

set -e

echo "==================================="
echo "Service Configuration Generator"
echo "==================================="
echo ""

# Example 1: Generate development webapp configuration
echo "1. Generating development webapp configuration..."
python -m service_manager config generate \
  --template service_config_template \
  --env dev \
  --output service_manager/configs/dev/webapp_generated.json \
  --param service_name=webapp \
  --param version=1.0.0 \
  --param port=3000 \
  --param max_memory=512M \
  --param healthcheck_endpoint=/health \
  --param healthcheck_interval=30s \
  --param healthcheck_timeout=5s

echo "✓ Generated: service_manager/configs/dev/webapp_generated.json"
echo ""

# Example 2: Generate production API configuration
echo "2. Generating production API configuration..."
python -m service_manager config generate \
  --template service_config_template \
  --env prod \
  --output service_manager/configs/prod/api_generated.json \
  --param service_name=api \
  --param version=3.2.0 \
  --param port=8443 \
  --param max_memory=4G \
  --param healthcheck_endpoint=/api/v1/health \
  --param healthcheck_interval=10s \
  --param healthcheck_timeout=5s

echo "✓ Generated: service_manager/configs/prod/api_generated.json"
echo ""

# Example 3: Generate monitoring configuration for development
echo "3. Generating development monitoring configuration..."
python -m service_manager config generate \
  --template monitoring_config_template \
  --env dev \
  --output service_manager/configs/dev/monitoring_generated.json \
  --param service_name=webapp \
  --param metrics_enabled=true \
  --param collection_interval=60s \
  --param retention_days=7 \
  --param alerts_enabled=true \
  --param cpu_threshold=75 \
  --param memory_threshold=80 \
  --param response_time_threshold=2000 \
  --param health_endpoint=/health \
  --param health_timeout=5s \
  --param expected_status=200

echo "✓ Generated: service_manager/configs/dev/monitoring_generated.json"
echo ""

echo "==================================="
echo "All configurations generated successfully!"
echo "==================================="
