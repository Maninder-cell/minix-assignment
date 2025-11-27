#!/bin/bash
# Example script: Perform batch operations across multiple hosts
# This demonstrates how to manage multiple services at once

set -e

echo "==================================="
echo "Batch Operations Script"
echo "==================================="
echo ""

# Define hosts and services
HOSTS=("dev-server1.example.com" "dev-server2.example.com" "dev-server3.example.com")
SERVICE_NAME="webapp"

# Function to check status on all hosts
check_all_status() {
  echo "Checking status on all hosts..."
  echo ""
  
  for host in "${HOSTS[@]}"; do
    echo "→ Checking $SERVICE_NAME on $host..."
    python -m service_manager status \
      --host "$host" \
      --service "$SERVICE_NAME" || {
        echo "  ✗ Failed to get status from $host"
        continue
      }
    echo ""
  done
}

# Function to start service on all hosts
start_all_services() {
  echo "Starting $SERVICE_NAME on all hosts..."
  echo ""
  
  for host in "${HOSTS[@]}"; do
    echo "→ Starting $SERVICE_NAME on $host..."
    python -m service_manager service start \
      --host "$host" \
      --service "$SERVICE_NAME" && {
        echo "  ✓ Service started on $host"
      } || {
        echo "  ✗ Failed to start service on $host"
      }
  done
  echo ""
}

# Function to stop service on all hosts
stop_all_services() {
  echo "Stopping $SERVICE_NAME on all hosts..."
  echo ""
  
  for host in "${HOSTS[@]}"; do
    echo "→ Stopping $SERVICE_NAME on $host..."
    python -m service_manager service stop \
      --host "$host" \
      --service "$SERVICE_NAME" && {
        echo "  ✓ Service stopped on $host"
      } || {
        echo "  ✗ Failed to stop service on $host"
      }
  done
  echo ""
}

# Function to deploy configuration to all hosts
deploy_to_all() {
  local config_file="$1"
  local remote_path="$2"
  
  echo "Deploying configuration to all hosts..."
  echo "Config: $config_file"
  echo "Remote path: $remote_path"
  echo ""
  
  for host in "${HOSTS[@]}"; do
    echo "→ Deploying to $host..."
    python -m service_manager deploy \
      --host "$host" \
      --config "$config_file" \
      --path "$remote_path" && {
        echo "  ✓ Deployed to $host"
      } || {
        echo "  ✗ Failed to deploy to $host"
      }
  done
  echo ""
}

# Main menu
echo "Select operation:"
echo "1. Check status on all hosts"
echo "2. Start service on all hosts"
echo "3. Stop service on all hosts"
echo "4. Deploy configuration to all hosts"
echo "5. Rolling restart (stop, deploy, start)"
echo ""

read -p "Enter choice [1-5]: " choice

case $choice in
  1)
    check_all_status
    ;;
  2)
    start_all_services
    check_all_status
    ;;
  3)
    stop_all_services
    check_all_status
    ;;
  4)
    read -p "Enter config file path: " config_file
    read -p "Enter remote path: " remote_path
    deploy_to_all "$config_file" "$remote_path"
    ;;
  5)
    read -p "Enter config file path: " config_file
    read -p "Enter remote path: " remote_path
    
    echo "Performing rolling restart..."
    echo ""
    
    for host in "${HOSTS[@]}"; do
      echo "→ Processing $host..."
      
      # Stop service
      echo "  Stopping service..."
      python -m service_manager service stop --host "$host" --service "$SERVICE_NAME" || true
      
      # Deploy configuration
      echo "  Deploying configuration..."
      python -m service_manager deploy --host "$host" --config "$config_file" --path "$remote_path"
      
      # Start service
      echo "  Starting service..."
      python -m service_manager service start --host "$host" --service "$SERVICE_NAME"
      
      # Verify
      echo "  Verifying status..."
      python -m service_manager status --host "$host" --service "$SERVICE_NAME"
      
      echo "  ✓ Completed $host"
      echo ""
      
      # Wait before next host
      sleep 5
    done
    
    echo "Rolling restart completed!"
    ;;
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo "==================================="
echo "Batch operation completed!"
echo "==================================="
