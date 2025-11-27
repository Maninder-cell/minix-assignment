#!/bin/bash
# Example script: Deploy service configuration to remote host
# This demonstrates a complete deployment workflow

set -e

# Configuration
SERVICE_NAME="${1:-webapp}"
ENVIRONMENT="${2:-dev}"
TARGET_HOST="${3:-dev-server.example.com}"
REMOTE_PATH="/etc/${SERVICE_NAME}/config.json"

echo "==================================="
echo "Service Deployment Script"
echo "==================================="
echo ""
echo "Service:     $SERVICE_NAME"
echo "Environment: $ENVIRONMENT"
echo "Target Host: $TARGET_HOST"
echo "Remote Path: $REMOTE_PATH"
echo ""

# Step 1: Generate configuration
echo "Step 1: Generating configuration..."
CONFIG_FILE="service_manager/configs/${ENVIRONMENT}/${SERVICE_NAME}_deploy.json"

if [ "$ENVIRONMENT" = "dev" ]; then
  python -m service_manager config generate \
    --template service_config_template \
    --env dev \
    --output "$CONFIG_FILE" \
    --param service_name="$SERVICE_NAME" \
    --param version=1.0.0 \
    --param port=3000 \
    --param max_memory=512M \
    --param healthcheck_endpoint=/health \
    --param healthcheck_interval=30s \
    --param healthcheck_timeout=5s
else
  python -m service_manager config generate \
    --template service_config_template \
    --env prod \
    --output "$CONFIG_FILE" \
    --param service_name="$SERVICE_NAME" \
    --param version=2.0.0 \
    --param port=8080 \
    --param max_memory=2G \
    --param healthcheck_endpoint=/health \
    --param healthcheck_interval=15s \
    --param healthcheck_timeout=5s
fi

echo "✓ Configuration generated: $CONFIG_FILE"
echo ""

# Step 2: Deploy configuration
echo "Step 2: Deploying configuration to $TARGET_HOST..."
python -m service_manager deploy \
  --host "$TARGET_HOST" \
  --config "$CONFIG_FILE" \
  --path "$REMOTE_PATH"

echo "✓ Configuration deployed"
echo ""

# Step 3: Restart service
echo "Step 3: Restarting service..."
python -m service_manager service stop --host "$TARGET_HOST" --service "$SERVICE_NAME" || true
sleep 2
python -m service_manager service start --host "$TARGET_HOST" --service "$SERVICE_NAME"

echo "✓ Service restarted"
echo ""

# Step 4: Verify service status
echo "Step 4: Verifying service status..."
python -m service_manager status --host "$TARGET_HOST" --service "$SERVICE_NAME"

echo ""
echo "==================================="
echo "Deployment completed successfully!"
echo "==================================="
