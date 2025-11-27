# Service Fleet Manager - Example Scripts

This directory contains example scripts demonstrating various use cases and workflows for the Service Fleet Manager.

## Available Scripts

### 1. generate_config.sh
Demonstrates how to generate service configurations from templates for different environments.

**Usage:**
```bash
./examples/generate_config.sh
```

**What it does:**
- Generates a development webapp configuration
- Generates a production API configuration
- Generates a development monitoring configuration

### 2. deploy_service.sh
Complete deployment workflow including configuration generation, deployment, and service restart.

**Usage:**
```bash
./examples/deploy_service.sh [service_name] [environment] [target_host]
```

**Examples:**
```bash
# Deploy webapp to development
./examples/deploy_service.sh webapp dev dev-server.example.com

# Deploy API to production
./examples/deploy_service.sh api prod prod-server.example.com
```

**What it does:**
1. Generates configuration from template
2. Deploys configuration to remote host
3. Restarts the service
4. Verifies service status

### 3. batch_operations.sh
Perform operations across multiple hosts simultaneously.

**Usage:**
```bash
./examples/batch_operations.sh
```

**Interactive menu options:**
1. Check status on all hosts
2. Start service on all hosts
3. Stop service on all hosts
4. Deploy configuration to all hosts
5. Rolling restart (stop, deploy, start)

**What it does:**
- Manages multiple service instances across different hosts
- Provides batch operations for common tasks
- Supports rolling restarts for zero-downtime deployments

### 4. monitor_services.sh
Collect metrics and generate reports for multiple services.

**Usage:**
```bash
./examples/monitor_services.sh
```

**What it does:**
- Collects metrics from configured services
- Generates human-readable reports
- Saves metrics and reports with timestamps
- Displays a summary of collected metrics

## Example Configurations

The `service_manager/configs/` directory contains example configurations:

### Development Environment (`dev/`)
- `example_webapp_params.json` - Parameters for webapp service
- `example_api_params.json` - Parameters for API service
- `example_monitoring_params.json` - Monitoring configuration parameters
- `webapp_config.json` - Sample generated webapp configuration

### Production Environment (`prod/`)
- `example_webapp_params.json` - Production webapp parameters
- `example_api_params.json` - Production API parameters
- `example_monitoring_params.json` - Production monitoring parameters
- `api_config.json` - Sample generated API configuration

## Using Parameter Files

Parameter files can be used to simplify configuration generation:

```bash
# Load parameters from JSON file
params=$(cat service_manager/configs/dev/example_webapp_params.json)

# Extract and use parameters
python -m service_manager config generate \
  --template service_config_template \
  --env dev \
  --output output.json \
  --param service_name=$(echo $params | jq -r .service_name) \
  --param version=$(echo $params | jq -r .version) \
  --param port=$(echo $params | jq -r .port) \
  --param max_memory=$(echo $params | jq -r .max_memory)
```

## Customizing Scripts

All scripts are designed to be easily customizable:

1. **Modify host lists**: Edit the `HOSTS` array in batch_operations.sh
2. **Change service names**: Update the `SERVICE_NAME` variable
3. **Adjust paths**: Modify `REMOTE_PATH` for different deployment locations
4. **Add monitoring targets**: Update the `SERVICES` associative array in monitor_services.sh

## Prerequisites

Before running these scripts:

1. Ensure Service Fleet Manager is installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure SSH access to target hosts:
   ```bash
   ssh-copy-id user@target-host
   ```

3. Make scripts executable:
   ```bash
   chmod +x examples/*.sh
   ```

4. Update host names and service names in scripts to match your environment

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitLab CI configuration
deploy:
  stage: deploy
  script:
    - ./examples/deploy_service.sh $SERVICE_NAME $CI_ENVIRONMENT_NAME $TARGET_HOST
  only:
    - main
```

## Troubleshooting

If scripts fail:

1. Check SSH connectivity:
   ```bash
   ssh target-host echo "Connection OK"
   ```

2. Verify service names:
   ```bash
   ssh target-host systemctl list-units --type=service
   ```

3. Check logs:
   ```bash
   tail -f service_manager.log
   ```

4. Run with verbose output:
   ```bash
   python -m service_manager -v status --host target-host --service myapp
   ```
