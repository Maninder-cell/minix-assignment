"""Monitoring System for Service Fleet Manager.

This module handles service metrics collection, report generation,
and notification sending for monitoring purposes.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from tabulate import tabulate

from service_manager.src.service_controller import ServiceController


logger = logging.getLogger(__name__)


class MonitoringSystem:
    """Monitors service health and generates reports.
    
    This class provides methods to collect service metrics, perform health checks,
    generate formatted reports, and send notifications.
    """
    
    def __init__(self, notification_config: Optional[Dict[str, Any]] = None):
        """Initialize monitoring system.
        
        Args:
            notification_config: Configuration for notifications (webhook URL, etc.)
                               Supported keys: webhook_url, mock_mode
        """
        self.notification_config = notification_config or {}
        self.service_controller = ServiceController()
        
        logger.info("MonitoringSystem initialized")
    
    def collect_metrics(
        self, 
        host: str, 
        service_name: str
    ) -> Dict[str, Any]:
        """Collect service metrics.
        
        Args:
            host: Remote host identifier
            service_name: Name of service
            
        Returns:
            Dictionary with metrics: status, uptime, health_check, timestamp
        """
        logger.info(f"Collecting metrics for service '{service_name}' on {host}")
        
        metrics = {
            'host': host,
            'service_name': service_name,
            'status': 'unknown',
            'uptime': None,
            'health_check': False,
            'health_endpoint': None,
            'response_time_ms': None,
            'timestamp': datetime.utcnow().isoformat(),
            'errors': []
        }
        
        try:
            # Get service status
            status_info = self.service_controller.check_service_status(
                host, service_name
            )
            
            metrics['status'] = status_info.get('status', 'unknown')
            metrics['uptime'] = status_info.get('uptime')
            
            # Perform health check if service is running
            if metrics['status'] == 'running':
                # Try to perform HTTP health check
                # Default to localhost:8080/health if not configured
                health_endpoint = f"http://{host}:8080/health"
                metrics['health_endpoint'] = health_endpoint
                
                health_result, response_time = self._perform_health_check(
                    health_endpoint
                )
                metrics['health_check'] = health_result
                metrics['response_time_ms'] = response_time
            
            logger.info(
                f"Successfully collected metrics for '{service_name}' on {host}"
            )
            
        except Exception as e:
            error_msg = f"Error collecting metrics: {str(e)}"
            logger.error(error_msg)
            metrics['errors'].append(error_msg)
        
        return metrics
    
    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """Generate human-readable report.
        
        Args:
            metrics: Metrics dictionary from collect_metrics
            
        Returns:
            Formatted report string with ASCII tables
        """
        logger.info("Generating metrics report")
        
        try:
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("SERVICE MONITORING REPORT")
            report_lines.append("=" * 60)
            report_lines.append("")
            
            # Basic information
            report_lines.append(f"Host: {metrics.get('host', 'N/A')}")
            report_lines.append(f"Service: {metrics.get('service_name', 'N/A')}")
            report_lines.append(f"Timestamp: {metrics.get('timestamp', 'N/A')}")
            report_lines.append("")
            
            # Service status table
            status_table = self._format_metrics_table(metrics)
            report_lines.append(status_table)
            report_lines.append("")
            
            # Errors section
            if metrics.get('errors'):
                report_lines.append("ERRORS:")
                for error in metrics['errors']:
                    report_lines.append(f"  - {error}")
                report_lines.append("")
            
            report_lines.append("=" * 60)
            
            report = "\n".join(report_lines)
            logger.info("Report generated successfully")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {str(e)}"
    
    def send_notification(
        self, 
        message: str, 
        severity: str
    ) -> bool:
        """Send notification.
        
        Args:
            message: Notification message
            severity: Severity level (info, warning, critical)
            
        Returns:
            True if sent successfully, False otherwise
        """
        logger.info(f"Sending notification with severity={severity}")
        
        try:
            # Format notification with timestamp and severity
            timestamp = datetime.utcnow().isoformat()
            formatted_message = (
                f"[{timestamp}] [{severity.upper()}] {message}"
            )
            
            # Check if mock mode is enabled
            if self.notification_config.get('mock_mode', True):
                return self._send_mock_notification(formatted_message)
            
            # Real notification via webhook
            webhook_url = self.notification_config.get('webhook_url')
            if not webhook_url:
                logger.warning("No webhook URL configured, using mock mode")
                return self._send_mock_notification(formatted_message)
            
            # Send to webhook
            response = requests.post(
                webhook_url,
                json={
                    'message': message,
                    'severity': severity,
                    'timestamp': timestamp
                },
                timeout=10
            )
            
            if response.status_code in [200, 201, 204]:
                logger.info("Notification sent successfully")
                return True
            else:
                logger.error(
                    f"Notification failed with status {response.status_code}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")
            return False
    
    def _perform_health_check(
        self, 
        health_endpoint: str, 
        timeout: int = 5
    ) -> tuple:
        """Perform HTTP health check.
        
        Args:
            health_endpoint: Health check URL
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (success: bool, response_time_ms: float or None)
        """
        logger.debug(f"Performing health check on {health_endpoint}")
        
        try:
            start_time = datetime.utcnow()
            response = requests.get(health_endpoint, timeout=timeout)
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                logger.debug(
                    f"Health check passed ({response_time:.2f}ms)"
                )
                return True, round(response_time, 2)
            else:
                logger.warning(
                    f"Health check failed with status {response.status_code}"
                )
                return False, round(response_time, 2)
                
        except requests.exceptions.Timeout:
            logger.warning(f"Health check timed out after {timeout}s")
            return False, None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Health check failed: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}")
            return False, None
    
    def _format_metrics_table(self, metrics: Dict[str, Any]) -> str:
        """Format metrics as ASCII table.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            Formatted ASCII table string
        """
        # Prepare table data
        table_data = [
            ["Metric", "Value"],
            ["Status", metrics.get('status', 'N/A')],
            ["Uptime", metrics.get('uptime', 'N/A')],
            ["Health Check", "✓ Pass" if metrics.get('health_check') else "✗ Fail"],
            ["Health Endpoint", metrics.get('health_endpoint', 'N/A')],
            [
                "Response Time", 
                f"{metrics.get('response_time_ms')}ms" 
                if metrics.get('response_time_ms') is not None 
                else 'N/A'
            ]
        ]
        
        # Generate table using tabulate
        table = tabulate(
            table_data[1:],  # Skip header row as tabulate adds its own
            headers=table_data[0],
            tablefmt='grid'
        )
        
        return table
    
    def _send_mock_notification(self, message: str) -> bool:
        """Send mock notification for testing.
        
        Args:
            message: Formatted notification message
            
        Returns:
            Always returns True
        """
        logger.info(f"[MOCK NOTIFICATION] {message}")
        print(f"[MOCK NOTIFICATION] {message}")
        return True
