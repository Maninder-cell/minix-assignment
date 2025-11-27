#!/bin/bash
# Example script: Monitor multiple services and generate reports
# This demonstrates monitoring and reporting capabilities

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
METRICS_DIR="metrics"
REPORTS_DIR="reports"

# Create directories if they don't exist
mkdir -p "$METRICS_DIR"
mkdir -p "$REPORTS_DIR"

echo "==================================="
echo "Service Monitoring Script"
echo "==================================="
echo "Timestamp: $TIMESTAMP"
echo ""

# Define services to monitor
declare -A SERVICES
SERVICES[dev-server.example.com]="webapp"
SERVICES[prod-server.example.com]="api"

# Collect metrics from all services
echo "Collecting metrics from services..."
echo ""

for host in "${!SERVICES[@]}"; do
  service="${SERVICES[$host]}"
  metrics_file="${METRICS_DIR}/${service}_${host}_${TIMESTAMP}.json"
  
  echo "→ Collecting metrics from $service on $host..."
  
  python -m service_manager monitor collect \
    --host "$host" \
    --service "$service" \
    --output "$metrics_file" || {
      echo "  ✗ Failed to collect metrics from $service on $host"
      continue
    }
  
  echo "  ✓ Metrics saved to $metrics_file"
  
  # Generate report
  report_file="${REPORTS_DIR}/${service}_${host}_${TIMESTAMP}.txt"
  
  echo "  → Generating report..."
  python -m service_manager monitor report \
    --metrics "$metrics_file" \
    --output "$report_file"
  
  echo "  ✓ Report saved to $report_file"
  echo ""
done

echo "==================================="
echo "Monitoring completed!"
echo ""
echo "Metrics saved in: $METRICS_DIR/"
echo "Reports saved in: $REPORTS_DIR/"
echo "==================================="

# Optional: Display summary
echo ""
echo "Summary of collected metrics:"
echo ""
for metrics_file in ${METRICS_DIR}/*_${TIMESTAMP}.json; do
  if [ -f "$metrics_file" ]; then
    echo "File: $(basename $metrics_file)"
    python -c "import json; data=json.load(open('$metrics_file')); print(f\"  Service: {data['service_name']}\n  Host: {data['host']}\n  Status: {data['status']}\n  Health Check: {'✓ Pass' if data['health_check'] else '✗ Fail'}\")"
    echo ""
  fi
done
