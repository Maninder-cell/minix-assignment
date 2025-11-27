#!/bin/bash
# Quick Start Guide - Run this to see Service Fleet Manager in action
# This script demonstrates basic functionality with mock/example data

set -e

echo "=============================================="
echo "Service Fleet Manager - Quick Start Guide"
echo "=============================================="
echo ""
echo "This script demonstrates the basic functionality"
echo "of the Service Fleet Manager using example data."
echo ""

# Check if running in correct directory
if [ ! -f "service_manager/__main__.py" ]; then
  echo "Error: Please run this script from the project root directory"
  exit 1
fi

# Step 1: Generate configurations
echo "Step 1: Generating Service Configurations"
echo "-------------------------------------------"
echo ""

echo "→ Generating development webapp configuration..."
python -m service_manager config generate \
  --template service_config_template \
  --env dev \
  --output service_manager/configs/dev/quickstart_webapp.json \
  --param service_name=webapp \
  --param version=1.0.0 \
  --param port=3000 \
  --param max_memory=512M \
  --param healthcheck_endpoint=/health \
  --param healthcheck_interval=30s \
  --param healthcheck_timeout=5s

echo "✓ Generated: service_manager/configs/dev/quickstart_webapp.json"
echo ""

echo "→ Generating production API configuration..."
python -m service_manager config generate \
  --template service_config_template \
  --env prod \
  --output service_manager/configs/prod/quickstart_api.json \
  --param service_name=api \
  --param version=2.0.0 \
  --param port=8080 \
  --param max_memory=2G \
  --param healthcheck_endpoint=/api/health \
  --param healthcheck_interval=15s \
  --param healthcheck_timeout=5s

echo "✓ Generated: service_manager/configs/prod/quickstart_api.json"
echo ""

echo "→ Generating monitoring configuration..."
python -m service_manager config generate \
  --template monitoring_config_template \
  --env dev \
  --output service_manager/configs/dev/quickstart_monitoring.json \
  --param service_name=webapp \
  --param metrics_enabled=true \
  --param collection_interval=60s \
  --param retention_days=7 \
  --param alerts_enabled=true \
  --param cpu_threshold=75 \
  --param memory_threshold=80 \
  --param response_time_threshold=2000

echo "✓ Generated: service_manager/configs/dev/quickstart_monitoring.json"
echo ""

# Step 2: View generated configurations
echo "Step 2: Viewing Generated Configurations"
echo "-------------------------------------------"
echo ""

echo "→ Development Webapp Configuration:"
cat service_manager/configs/dev/quickstart_webapp.json | python -m json.tool
echo ""

echo "→ Production API Configuration:"
cat service_manager/configs/prod/quickstart_api.json | python -m json.tool
echo ""

# Step 3: Show help for other commands
echo "Step 3: Available Commands"
echo "-------------------------------------------"
echo ""

echo "The Service Fleet Manager provides the following commands:"
echo ""
echo "1. Configuration Management:"
echo "   python -m service_manager config generate --help"
echo ""
echo "2. Deployment:"
echo "   python -m service_manager deploy --help"
echo ""
echo "3. Service Status:"
echo "   python -m service_manager status --help"
echo ""
echo "4. Service Control:"
echo "   python -m service_manager service start --help"
echo "   python -m service_manager service stop --help"
echo ""
echo "5. Monitoring:"
echo "   python -m service_manager monitor collect --help"
echo "   python -m service_manager monitor report --help"
echo ""

# Step 4: Next steps
echo "Step 4: Next Steps"
echo "-------------------------------------------"
echo ""
echo "To use the Service Fleet Manager with real hosts:"
echo ""
echo "1. Configure SSH access to your target hosts:"
echo "   ssh-copy-id user@your-host.example.com"
echo ""
echo "2. Deploy a configuration:"
echo "   python -m service_manager deploy \\"
echo "     --host your-host.example.com \\"
echo "     --config service_manager/configs/dev/quickstart_webapp.json \\"
echo "     --path /etc/webapp/config.json"
echo ""
echo "3. Check service status:"
echo "   python -m service_manager status \\"
echo "     --host your-host.example.com \\"
echo "     --service webapp"
echo ""
echo "4. Start a service:"
echo "   python -m service_manager service start \\"
echo "     --host your-host.example.com \\"
echo "     --service webapp"
echo ""
echo "5. Collect metrics:"
echo "   python -m service_manager monitor collect \\"
echo "     --host your-host.example.com \\"
echo "     --service webapp \\"
echo "     --output metrics/webapp-metrics.json"
echo ""

echo "=============================================="
echo "Quick Start Complete!"
echo "=============================================="
echo ""
echo "Generated configurations are in:"
echo "  - service_manager/configs/dev/"
echo "  - service_manager/configs/prod/"
echo ""
echo "For more examples, see the scripts in examples/"
echo "For detailed documentation, see README.md"
echo ""
