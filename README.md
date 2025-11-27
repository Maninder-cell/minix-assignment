# Service Fleet Manager

A Python-based command-line tool for managing a small fleet of service instances across multiple environments. The Service Fleet Manager provides infrastructure automation capabilities through configuration management, remote service control, and monitoring features.

## Features

- **Configuration Management**: Generate service configurations from Jinja2 templates for different environments (dev/prod)
- **Remote Service Control**: Start, stop, and check status of services on remote hosts via SSH
- **Monitoring & Reporting**: Collect service metrics, perform health checks, and generate formatted reports
- **Notification System**: Send notifications for service state changes with configurable severity levels
- **CLI Interface**: User-friendly command-line interface for all operations

## Project Structure

```
service_manager/
├── configs/
│   ├── templates/     # Jinja2 configuration templates
│   │   ├── service_config_template.json
│   │   └── monitoring_config_template.json
│   ├── dev/          # Development environment configs
│   └── prod/         # Production environment configs
├── src/
│   ├── utils/        # Utility modules
│   │   ├── ssh.py           # SSH connection management
│   │   └── validators.py    # Configuration validators
│   ├── config_manager.py    # Configuration generation and deployment
│   ├── service_controller.py # Service lifecycle control
│   └── monitoring.py        # Metrics collection and reporting
└── __main__.py       # CLI entry point

tests/                # Unit and integration tests
```

## Installation

### Prerequisites

- Python 3.8 or higher
- SSH access to target hosts with key-based authentication
- Network connectivity to remote hosts

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd service-fleet-manager
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On Linux/macOS:
   ```bash
   source venv/bin/activate
   ```
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify installation**
   ```bash
   python -m service_manager --version
   ```

### SSH Configuration

Ensure you have SSH key-based authentication configured for your target hosts:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy your public key to target hosts
ssh-copy-id user@target-host
```

## Usage

### General Command Structure

```bash
python -m service_manager [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**
- `-v, --verbose`: Enable verbose logging output
- `-q, --quiet`: Suppress all output except errors
- `--version`: Show version and exit
- `--help`: Show help message and exit

### Configuration Management

#### Generate Configuration from Template

Generate a service configuration from a Jinja2 template:

```bash
python -m service_manager config generate \
  --template service_config_template \
  --env dev \
  --output configs/dev/myapp.json \
  --param service_name=myapp \
  --param port=8080 \
  --param version=1.0.0 \
  --param max_memory=512M
```

**Options:**
- `-t, --template`: Name of the configuration template (without .json extension)
- `-e, --env`: Target environment (`dev` or `prod`)
- `-o, --output`: Output path for generated configuration file
- `-p, --param`: Template parameters in `key=value` format (can be used multiple times)

**Example:**
```bash
# Generate development configuration
python -m service_manager config generate \
  -t service_config_template \
  -e dev \
  -o configs/dev/webapp.json \
  -p service_name=webapp \
  -p port=3000

# Generate production configuration with more parameters
python -m service_manager config generate \
  -t service_config_template \
  -e prod \
  -o configs/prod/api.json \
  -p service_name=api \
  -p port=8080 \
  -p version=2.1.0 \
  -p max_memory=1G
```

### Configuration Deployment

#### Deploy Configuration to Remote Host

Deploy a generated configuration file to a remote host:

```bash
python -m service_manager deploy \
  --host server1.example.com \
  --config configs/dev/myapp.json \
  --path /etc/myapp/config.json
```

**Options:**
- `-h, --host`: Target host identifier (hostname or IP address)
- `-c, --config`: Path to configuration file to deploy
- `-p, --path`: Remote path where configuration should be deployed

**Example:**
```bash
# Deploy to development server
python -m service_manager deploy \
  -h dev-server.example.com \
  -c configs/dev/webapp.json \
  -p /opt/webapp/config.json

# Deploy to production with user@host format
python -m service_manager deploy \
  -h deploy@prod-server.example.com \
  -c configs/prod/api.json \
  -p /etc/api/config.json
```

### Service Control

#### Check Service Status

Check the status of a service on a remote host:

```bash
python -m service_manager status \
  --host server1.example.com \
  --service myapp
```

**Options:**
- `-h, --host`: Target host identifier
- `-s, --service`: Name of the service to check

**Example Output:**
```
============================================================
SERVICE STATUS
============================================================
Service:       myapp
Status:        RUNNING
PID:           12345
Uptime:        2h 15m
Memory Usage:  256M
Timestamp:     2025-11-26T10:30:00.000000
============================================================
```

**Exit Codes:**
- `0`: Service is running
- `1`: Error occurred
- `3`: Service is stopped

#### Start Service

Start a service on a remote host:

```bash
python -m service_manager service start \
  --host server1.example.com \
  --service myapp
```

**Options:**
- `-h, --host`: Target host identifier
- `-s, --service`: Name of the service to start

**Example:**
```bash
# Start service on development server
python -m service_manager service start -h dev-server -s webapp

# Start service with verbose logging
python -m service_manager -v service start -h prod-server -s api
```

#### Stop Service

Stop a service on a remote host:

```bash
python -m service_manager service stop \
  --host server1.example.com \
  --service myapp
```

**Options:**
- `-h, --host`: Target host identifier
- `-s, --service`: Name of the service to stop

**Example:**
```bash
# Stop service on development server
python -m service_manager service stop -h dev-server -s webapp

# Stop service with quiet mode (only errors shown)
python -m service_manager -q service stop -h prod-server -s api
```

### Monitoring and Reporting

#### Collect Service Metrics

Collect metrics from a service on a remote host:

```bash
python -m service_manager monitor collect \
  --host server1.example.com \
  --service myapp \
  --output metrics/myapp-metrics.json
```

**Options:**
- `-h, --host`: Target host identifier
- `-s, --service`: Name of the service to monitor
- `-o, --output`: Output file to save metrics (JSON format, optional)

**Example:**
```bash
# Collect metrics and save to file
python -m service_manager monitor collect \
  -h prod-server \
  -s api \
  -o metrics/api-$(date +%Y%m%d).json

# Collect metrics and display to console
python -m service_manager monitor collect -h dev-server -s webapp
```

**Metrics Output:**
```json
{
  "host": "server1.example.com",
  "service_name": "myapp",
  "status": "running",
  "uptime": "2h 15m",
  "health_check": true,
  "health_endpoint": "http://server1.example.com:8080/health",
  "response_time_ms": 45.23,
  "timestamp": "2025-11-26T10:30:00.000000",
  "errors": []
}
```

#### Generate Report from Metrics

Generate a human-readable report from collected metrics:

```bash
python -m service_manager monitor report \
  --metrics metrics/myapp-metrics.json \
  --output reports/myapp-report.txt
```

**Options:**
- `-m, --metrics`: Path to metrics file (JSON format)
- `-o, --output`: Output file to save report (text format, optional)

**Example:**
```bash
# Generate report and save to file
python -m service_manager monitor report \
  -m metrics/api-20251126.json \
  -o reports/api-report-20251126.txt

# Generate report and display to console
python -m service_manager monitor report -m metrics/webapp-metrics.json
```

**Report Output:**
```
============================================================
SERVICE MONITORING REPORT
============================================================

Host: server1.example.com
Service: myapp
Timestamp: 2025-11-26T10:30:00.000000

+------------------+------------------------------------------+
| Metric           | Value                                    |
+==================+==========================================+
| Status           | running                                  |
+------------------+------------------------------------------+
| Uptime           | 2h 15m                                   |
+------------------+------------------------------------------+
| Health Check     | ✓ Pass                                   |
+------------------+------------------------------------------+
| Health Endpoint  | http://server1.example.com:8080/health   |
+------------------+------------------------------------------+
| Response Time    | 45.23ms                                  |
+------------------+------------------------------------------+

============================================================
```

## Configuration Templates

Configuration templates use Jinja2 syntax for variable substitution. Templates are stored in `service_manager/configs/templates/`.

### Service Configuration Template

**File:** `service_config_template.json`

```json
{
  "service": {
    "name": "{{ service_name }}",
    "version": "{{ version }}",
    "env": "{{ env }}",
    "port": {{ port }},
    "max_memory": "{{ max_memory }}",
    "healthcheck": {
      "endpoint": "/health",
      "interval": "30s",
      "timeout": "5s"
    }
  }
}
```

**Required Parameters:**
- `service_name`: Name of the service
- `version`: Service version string
- `env`: Environment (dev/prod) - automatically added
- `port`: Service port number (integer)
- `max_memory`: Memory limit (e.g., "512M", "1G")

### Monitoring Configuration Template

**File:** `monitoring_config_template.json`

```json
{
  "monitoring": {
    "service_name": "{{ service_name }}",
    "env": "{{ env }}",
    "metrics": {
      "enabled": true,
      "interval": "{{ metrics_interval | default('60s') }}",
      "retention": "{{ metrics_retention | default('7d') }}"
    },
    "alerts": {
      "enabled": {{ alerts_enabled | default('true') }},
      "webhook_url": "{{ webhook_url | default('') }}"
    }
  }
}
```

**Required Parameters:**
- `service_name`: Name of the service
- `env`: Environment (dev/prod) - automatically added

**Optional Parameters:**
- `metrics_interval`: Metrics collection interval (default: "60s")
- `metrics_retention`: Metrics retention period (default: "7d")
- `alerts_enabled`: Enable alerts (default: true)
- `webhook_url`: Webhook URL for notifications (default: empty)

### Creating Custom Templates

1. Create a new `.json` file in `service_manager/configs/templates/`
2. Use Jinja2 syntax for variables: `{{ variable_name }}`
3. Use filters for defaults: `{{ variable | default('default_value') }}`
4. Reference the template by name (without .json extension) in CLI commands

## Logging

All operations are logged to `service_manager.log` in the current directory. Log levels:

- **DEBUG**: Detailed execution flow (use `-v` flag)
- **INFO**: Operation start/completion, status changes
- **WARNING**: Retries, degraded functionality
- **ERROR**: Operation failures, exceptions
- **CRITICAL**: System-level failures

**View logs:**
```bash
# View recent logs
tail -f service_manager.log

# Search for errors
grep ERROR service_manager.log

# View logs for specific service
grep "myapp" service_manager.log
```

## Advanced Usage

### Batch Operations

Process multiple hosts using shell scripting:

```bash
# Check status on multiple hosts
for host in server1 server2 server3; do
  echo "Checking $host..."
  python -m service_manager status -h $host -s myapp
done

# Deploy configuration to multiple hosts
for host in $(cat hosts.txt); do
  python -m service_manager deploy -h $host -c config.json -p /etc/app/config.json
done
```

### Automated Monitoring

Set up a cron job for periodic monitoring:

```bash
# Add to crontab (crontab -e)
# Collect metrics every 5 minutes
*/5 * * * * cd /path/to/service-fleet-manager && python -m service_manager monitor collect -h prod-server -s api -o metrics/api-$(date +\%Y\%m\%d-\%H\%M).json

# Generate daily report at midnight
0 0 * * * cd /path/to/service-fleet-manager && python -m service_manager monitor report -m metrics/api-latest.json -o reports/daily-$(date +\%Y\%m\%d).txt
```

### Integration with CI/CD

Use in deployment pipelines:

```bash
#!/bin/bash
# deploy.sh

set -e

# Generate configuration
python -m service_manager config generate \
  -t service_config_template \
  -e prod \
  -o config.json \
  -p service_name=$SERVICE_NAME \
  -p version=$VERSION \
  -p port=$PORT

# Deploy configuration
python -m service_manager deploy \
  -h $TARGET_HOST \
  -c config.json \
  -p /etc/$SERVICE_NAME/config.json

# Restart service
python -m service_manager service stop -h $TARGET_HOST -s $SERVICE_NAME
python -m service_manager service start -h $TARGET_HOST -s $SERVICE_NAME

# Verify service is running
python -m service_manager status -h $TARGET_HOST -s $SERVICE_NAME
```