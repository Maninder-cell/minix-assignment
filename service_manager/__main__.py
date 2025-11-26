"""Service Fleet Manager CLI.

Command-line interface for managing service instances across multiple hosts.
"""

import json
import logging
import sys
from pathlib import Path

import click

from service_manager.src.config_manager import (
    ConfigurationManager,
    TemplateNotFoundError,
    TemplateRenderError,
    ValidationError
)
from service_manager.src.service_controller import ServiceController
from service_manager.src.monitoring import MonitoringSystem


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('service_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging output'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress all output except errors'
)
@click.version_option(version='1.0.0', prog_name='Service Fleet Manager')
def cli(verbose, quiet):
    """Service Fleet Manager - Manage service instances across multiple hosts.
    
    This tool provides configuration management, remote service control,
    and monitoring capabilities for your service fleet.
    
    Use --help with any command to see detailed usage information.
    """
    # Adjust logging level based on flags
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


@cli.group()
def config():
    """Configuration management commands.
    
    Generate and validate service configurations from templates.
    """
    pass


@config.command('generate')
@click.option(
    '--template', '-t',
    required=True,
    help='Name of the configuration template (without .json extension)'
)
@click.option(
    '--env', '-e',
    required=True,
    type=click.Choice(['dev', 'prod'], case_sensitive=False),
    help='Target environment (dev or prod)'
)
@click.option(
    '--output', '-o',
    required=True,
    type=click.Path(),
    help='Output path for generated configuration file'
)
@click.option(
    '--param', '-p',
    multiple=True,
    help='Template parameters in key=value format (can be used multiple times)'
)
def config_generate(template, env, output, param):
    """Generate configuration from template.
    
    Example:
        service_manager config generate -t service_config_template -e dev -o config.json -p service_name=myapp -p port=8080
    """
    try:
        # Parse parameters
        params = {}
        for p in param:
            if '=' not in p:
                click.echo(
                    f"Error: Invalid parameter format '{p}'. "
                    f"Use key=value format.",
                    err=True
                )
                sys.exit(1)
            
            key, value = p.split('=', 1)
            params[key.strip()] = value.strip()
        
        # Initialize ConfigurationManager
        template_dir = 'service_manager/configs/templates'
        config_dir = f'service_manager/configs/{env}'
        
        config_manager = ConfigurationManager(template_dir, config_dir)
        
        # Generate configuration
        click.echo(f"Generating configuration from template '{template}' for {env} environment...")
        config = config_manager.generate_config(template, env, params)
        
        # Validate configuration
        click.echo("Validating configuration...")
        if not config_manager.validate_config(config):
            click.echo(
                "Warning: Configuration validation failed. "
                "The configuration may be incomplete or invalid.",
                err=True
            )
        
        # Save configuration to output file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        click.echo(f"✓ Configuration successfully generated and saved to: {output}")
        
    except TemplateNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            f"Available templates should be in: {template_dir}",
            err=True
        )
        sys.exit(1)
    except TemplateRenderError as e:
        click.echo(f"Error rendering template: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Unexpected error during config generation")
        sys.exit(1)


@cli.command('deploy')
@click.option(
    '--host', '-h',
    required=True,
    help='Target host identifier (hostname or IP address)'
)
@click.option(
    '--config', '-c',
    required=True,
    type=click.Path(exists=True),
    help='Path to configuration file to deploy'
)
@click.option(
    '--path', '-p',
    required=True,
    help='Remote path where configuration should be deployed'
)
def deploy(host, config, path):
    """Deploy configuration to remote host.
    
    Example:
        service_manager deploy -h server1.example.com -c config.json -p /etc/myapp/config.json
    """
    try:
        # Load configuration file
        click.echo(f"Loading configuration from {config}...")
        with open(config, 'r') as f:
            config_data = json.load(f)
        
        # Initialize ConfigurationManager
        template_dir = 'service_manager/configs/templates'
        config_dir = 'service_manager/configs'
        
        config_manager = ConfigurationManager(template_dir, config_dir)
        
        # Deploy configuration
        click.echo(f"Deploying configuration to {host}:{path}...")
        success = config_manager.deploy_config(config_data, host, path)
        
        if success:
            click.echo(f"✓ Configuration successfully deployed to {host}:{path}")
        else:
            click.echo(
                f"✗ Failed to deploy configuration to {host}:{path}",
                err=True
            )
            click.echo(
                "Check the log file for details: service_manager.log",
                err=True
            )
            sys.exit(1)
        
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in configuration file: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: Configuration file not found: {config}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Unexpected error during deployment")
        sys.exit(1)


@cli.command('status')
@click.option(
    '--host', '-h',
    required=True,
    help='Target host identifier (hostname or IP address)'
)
@click.option(
    '--service', '-s',
    required=True,
    help='Name of the service to check'
)
def status(host, service):
    """Check service status on remote host.
    
    Example:
        service_manager status -h server1.example.com -s myapp
    """
    try:
        # Initialize ServiceController
        service_controller = ServiceController()
        
        # Check service status
        click.echo(f"Checking status of service '{service}' on {host}...")
        status_info = service_controller.check_service_status(host, service)
        
        # Display formatted status
        click.echo("\n" + "=" * 60)
        click.echo("SERVICE STATUS")
        click.echo("=" * 60)
        click.echo(f"Service:       {status_info['service_name']}")
        click.echo(f"Status:        {status_info['status'].upper()}")
        click.echo(f"PID:           {status_info['pid'] or 'N/A'}")
        click.echo(f"Uptime:        {status_info['uptime'] or 'N/A'}")
        click.echo(f"Memory Usage:  {status_info['memory_usage'] or 'N/A'}")
        click.echo(f"Timestamp:     {status_info['timestamp']}")
        click.echo("=" * 60 + "\n")
        
        # Exit with appropriate code
        if status_info['status'] in ['running']:
            sys.exit(0)
        elif status_info['status'] in ['stopped', 'inactive']:
            sys.exit(3)
        else:
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Unexpected error checking service status")
        sys.exit(1)


@cli.group()
def service():
    """Service control commands.
    
    Start, stop, and manage services on remote hosts.
    """
    pass


@service.command('start')
@click.option(
    '--host', '-h',
    required=True,
    help='Target host identifier (hostname or IP address)'
)
@click.option(
    '--service', '-s',
    required=True,
    help='Name of the service to start'
)
def service_start(host, service):
    """Start service on remote host.
    
    Example:
        service_manager service start -h server1.example.com -s myapp
    """
    try:
        # Initialize ServiceController
        service_controller = ServiceController()
        
        # Start service
        click.echo(f"Starting service '{service}' on {host}...")
        success = service_controller.start_service(host, service)
        
        if success:
            click.echo(f"✓ Service '{service}' started successfully on {host}")
        else:
            click.echo(
                f"✗ Failed to start service '{service}' on {host}",
                err=True
            )
            click.echo(
                "Check the log file for details: service_manager.log",
                err=True
            )
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Unexpected error starting service")
        sys.exit(1)


@service.command('stop')
@click.option(
    '--host', '-h',
    required=True,
    help='Target host identifier (hostname or IP address)'
)
@click.option(
    '--service', '-s',
    required=True,
    help='Name of the service to stop'
)
def service_stop(host, service):
    """Stop service on remote host.
    
    Example:
        service_manager service stop -h server1.example.com -s myapp
    """
    try:
        # Initialize ServiceController
        service_controller = ServiceController()
        
        # Stop service
        click.echo(f"Stopping service '{service}' on {host}...")
        success = service_controller.stop_service(host, service)
        
        if success:
            click.echo(f"✓ Service '{service}' stopped successfully on {host}")
        else:
            click.echo(
                f"✗ Failed to stop service '{service}' on {host}",
                err=True
            )
            click.echo(
                "Check the log file for details: service_manager.log",
                err=True
            )
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Unexpected error stopping service")
        sys.exit(1)


@cli.group()
def monitor():
    """Monitoring and reporting commands.
    
    Collect metrics and generate reports for service monitoring.
    """
    pass


@monitor.command('collect')
@click.option(
    '--host', '-h',
    required=True,
    help='Target host identifier (hostname or IP address)'
)
@click.option(
    '--service', '-s',
    required=True,
    help='Name of the service to monitor'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file to save metrics (JSON format)'
)
def monitor_collect(host, service, output):
    """Collect service metrics from remote host.
    
    Example:
        service_manager monitor collect -h server1.example.com -s myapp -o metrics.json
    """
    try:
        # Initialize MonitoringSystem
        monitoring_system = MonitoringSystem()
        
        # Collect metrics
        click.echo(f"Collecting metrics for service '{service}' on {host}...")
        metrics = monitoring_system.collect_metrics(host, service)
        
        # Display summary
        click.echo(f"\n✓ Metrics collected successfully")
        click.echo(f"  Status: {metrics['status']}")
        click.echo(f"  Health Check: {'✓ Pass' if metrics['health_check'] else '✗ Fail'}")
        
        # Save to file if output specified
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            click.echo(f"  Metrics saved to: {output}")
        else:
            # Display metrics as JSON
            click.echo("\nMetrics:")
            click.echo(json.dumps(metrics, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Unexpected error collecting metrics")
        sys.exit(1)


@monitor.command('report')
@click.option(
    '--metrics', '-m',
    required=True,
    type=click.Path(exists=True),
    help='Path to metrics file (JSON format)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file to save report (text format)'
)
def monitor_report(metrics, output):
    """Generate human-readable report from metrics.
    
    Example:
        service_manager monitor report -m metrics.json -o report.txt
    """
    try:
        # Load metrics file
        click.echo(f"Loading metrics from {metrics}...")
        with open(metrics, 'r') as f:
            metrics_data = json.load(f)
        
        # Initialize MonitoringSystem
        monitoring_system = MonitoringSystem()
        
        # Generate report
        click.echo("Generating report...")
        report = monitoring_system.generate_report(metrics_data)
        
        # Save to file if output specified
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(report)
            
            click.echo(f"✓ Report saved to: {output}")
        
        # Always display report to console
        click.echo("\n" + report)
        
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in metrics file: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: Metrics file not found: {metrics}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Unexpected error generating report")
        sys.exit(1)


if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
