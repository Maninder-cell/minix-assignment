#!/bin/bash
# Manual Integration Test Script
# Tests the complete workflow of the Service Fleet Manager

set -e

echo "=============================================="
echo "Service Fleet Manager - Integration Test"
echo "=============================================="
echo ""

# Detect if we're running from tests/ directory or project root
if [ -f "service_manager/__main__.py" ]; then
    # Running from project root
    PROJECT_ROOT="."
elif [ -f "../service_manager/__main__.py" ]; then
    # Running from tests/ directory
    PROJECT_ROOT=".."
    cd "$PROJECT_ROOT"
else
    echo "Error: Cannot find project root. Please run from project root or tests/ directory."
    exit 1
fi

echo "Running from: $(pwd)"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_DIR="test_output_${TIMESTAMP}"
mkdir -p "$TEST_DIR"

echo "Test output directory: $TEST_DIR"
echo ""

# Test 1: Configuration Generation
echo "Test 1: Configuration Generation"
echo "-------------------------------------------"
python -m service_manager config generate \
  --template service_config_template \
  --env dev \
  --output "$TEST_DIR/test_config.json" \
  --param service_name=test_service \
  --param version=1.0.0 \
  --param port=9000 \
  --param max_memory=256M \
  --param healthcheck_endpoint=/health \
  --param healthcheck_interval=30s \
  --param healthcheck_timeout=5s 2>&1 | grep -E "(✓|Error)" || true

if [ -f "$TEST_DIR/test_config.json" ]; then
  echo "✓ Test 1 PASSED: Configuration file created"
else
  echo "✗ Test 1 FAILED: Configuration file not created"
  exit 1
fi
echo ""

# Test 2: Configuration Validation (JSON format)
echo "Test 2: Configuration Validation"
echo "-------------------------------------------"
if python -m json.tool "$TEST_DIR/test_config.json" > /dev/null 2>&1; then
  echo "✓ Test 2 PASSED: Configuration is valid JSON"
else
  echo "✗ Test 2 FAILED: Configuration is not valid JSON"
  exit 1
fi
echo ""

# Test 3: Error Handling - Invalid Template
echo "Test 3: Error Handling - Invalid Template"
echo "-------------------------------------------"
if python -m service_manager config generate \
  --template nonexistent_template \
  --env dev \
  --output "$TEST_DIR/should_not_exist.json" 2>&1 | grep -q "not found"; then
  echo "✓ Test 3 PASSED: Error handling works correctly"
else
  echo "✗ Test 3 FAILED: Error handling not working"
  exit 1
fi
echo ""

# Test 4: Help Commands
echo "Test 4: Help Commands"
echo "-------------------------------------------"
if python -m service_manager --help > /dev/null 2>&1; then
  echo "✓ Test 4a PASSED: Main help command works"
else
  echo "✗ Test 4a FAILED: Main help command failed"
  exit 1
fi

if python -m service_manager config generate --help > /dev/null 2>&1; then
  echo "✓ Test 4b PASSED: Config generate help works"
else
  echo "✗ Test 4b FAILED: Config generate help failed"
  exit 1
fi

if python -m service_manager deploy --help > /dev/null 2>&1; then
  echo "✓ Test 4c PASSED: Deploy help works"
else
  echo "✗ Test 4c FAILED: Deploy help failed"
  exit 1
fi

if python -m service_manager status --help > /dev/null 2>&1; then
  echo "✓ Test 4d PASSED: Status help works"
else
  echo "✗ Test 4d FAILED: Status help failed"
  exit 1
fi

if python -m service_manager service start --help > /dev/null 2>&1; then
  echo "✓ Test 4e PASSED: Service start help works"
else
  echo "✗ Test 4e FAILED: Service start help failed"
  exit 1
fi

if python -m service_manager monitor collect --help > /dev/null 2>&1; then
  echo "✓ Test 4f PASSED: Monitor collect help works"
else
  echo "✗ Test 4f FAILED: Monitor collect help failed"
  exit 1
fi
echo ""

# Test 5: Logging
echo "Test 5: Logging Verification"
echo "-------------------------------------------"
if [ -f "service_manager.log" ]; then
  echo "✓ Test 5a PASSED: Log file exists"
  
  if grep -q "INFO" service_manager.log; then
    echo "✓ Test 5b PASSED: INFO level logging works"
  else
    echo "✗ Test 5b FAILED: INFO level logging not found"
  fi
  
  if grep -q "ConfigurationManager" service_manager.log; then
    echo "✓ Test 5c PASSED: Component logging works"
  else
    echo "✗ Test 5c FAILED: Component logging not found"
  fi
else
  echo "✗ Test 5a FAILED: Log file does not exist"
  exit 1
fi
echo ""

# Test 6: Multiple Environment Support
echo "Test 6: Multiple Environment Support"
echo "-------------------------------------------"
python -m service_manager config generate \
  --template service_config_template \
  --env prod \
  --output "$TEST_DIR/prod_config.json" \
  --param service_name=prod_service \
  --param version=2.0.0 \
  --param port=8080 \
  --param max_memory=1G \
  --param healthcheck_endpoint=/health \
  --param healthcheck_interval=15s \
  --param healthcheck_timeout=5s 2>&1 | grep -E "(✓|Error)" || true

if [ -f "$TEST_DIR/prod_config.json" ]; then
  if grep -q '"env": "prod"' "$TEST_DIR/prod_config.json"; then
    echo "✓ Test 6 PASSED: Production environment configuration works"
  else
    echo "✗ Test 6 FAILED: Production environment not set correctly"
    exit 1
  fi
else
  echo "✗ Test 6 FAILED: Production configuration not created"
  exit 1
fi
echo ""

# Test 7: Parameter Handling
echo "Test 7: Parameter Handling"
echo "-------------------------------------------"
python -m service_manager config generate \
  --template service_config_template \
  --env dev \
  --output "$TEST_DIR/param_test.json" \
  --param service_name=param_test \
  --param version=3.0.0 \
  --param port=7777 \
  --param max_memory=128M \
  --param healthcheck_endpoint=/custom/health \
  --param healthcheck_interval=45s \
  --param healthcheck_timeout=10s 2>&1 | grep -E "(✓|Error)" || true

if grep -q '"port": 7777' "$TEST_DIR/param_test.json" && \
   grep -q '"version": "3.0.0"' "$TEST_DIR/param_test.json" && \
   grep -q '"max_memory": "128M"' "$TEST_DIR/param_test.json"; then
  echo "✓ Test 7 PASSED: Parameters are correctly substituted"
else
  echo "✗ Test 7 FAILED: Parameters not substituted correctly"
  exit 1
fi
echo ""

# Summary
echo "=============================================="
echo "Integration Test Summary"
echo "=============================================="
echo "All tests PASSED ✓"
echo ""
echo "Test artifacts saved in: $TEST_DIR"
echo "Log file: service_manager.log"
echo "=============================================="
