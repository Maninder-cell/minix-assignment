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
│   ├── dev/          # Development environment configs
│   └── prod/         # Production environment configs
├── src/
│   ├── utils/        # Utility modules (SSH, validators)
│   ├── config_manager.py
│   ├── service_controller.py
│   └── monitoring.py
└── __main__.py       # CLI entry point

tests/                # Unit and integration tests
```

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```