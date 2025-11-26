"""Service Controller for Service Fleet Manager.

This module handles remote service operations including status checks,
starting, and stopping services on remote hosts.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional

from service_manager.src.utils.ssh import SSHConnectionManager


logger = logging.getLogger(__name__)


class ServiceManagerError(Exception):
    """Base exception for all service manager errors."""
    pass


class RemoteExecutionError(ServiceManagerError):
    """Exception raised when remote command execution fails."""
    pass


class ConnectionError(RemoteExecutionError):
    """Exception raised when SSH connection fails."""
    pass


class TimeoutError(RemoteExecutionError):
    """Exception raised when operation times out."""
    pass


class ServiceOperationError(ServiceManagerError):
    """Exception raised when service operation fails."""
    pass


class ServiceController:
    """Controls service lifecycle operations on remote hosts.
    
    This class provides methods to check service status, start, and stop
    services on remote hosts via SSH connections.
    """
    
    def __init__(self, ssh_config: Optional[Dict[str, Any]] = None):
        """Initialize service controller.
        
        Args:
            ssh_config: Optional SSH configuration (timeout, retries, etc.)
                       Supported keys: max_retries, retry_delay, timeout
        """
        ssh_config = ssh_config or {}
        
        self.ssh_manager = SSHConnectionManager(
            max_retries=ssh_config.get('max_retries', 3),
            retry_delay=ssh_config.get('retry_delay', 1.0),
            timeout=ssh_config.get('timeout', 30)
        )
        
        logger.info("ServiceController initialized")
    
    def check_service_status(
        self, 
        host: str, 
        service_name: str
    ) -> Dict[str, Any]:
        """Check service status on remote host.
        
        Args:
            host: Remote host identifier
            service_name: Name of service to check
            
        Returns:
            Dictionary with keys: service_name, status, pid, uptime, 
            memory_usage, timestamp
            
        Raises:
            ConnectionError: If unable to connect
            TimeoutError: If operation times out
        """
        logger.info(f"Checking status of service '{service_name}' on {host}")
        
        try:
            # Execute systemctl status command
            command = f"systemctl status {service_name}"
            stdout, stderr, exit_code = self._execute_remote_command(
                host, command
            )
            
            # Parse the status output
            status_dict = self._parse_service_status(
                stdout, stderr, exit_code, service_name
            )
            
            logger.info(
                f"Service '{service_name}' on {host} is {status_dict['status']}"
            )
            return status_dict
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to check service status: {e}")
            # Return error status instead of raising
            return {
                'service_name': service_name,
                'status': 'error',
                'pid': None,
                'uptime': None,
                'memory_usage': None,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error checking service status: {e}")
            return {
                'service_name': service_name,
                'status': 'unknown',
                'pid': None,
                'uptime': None,
                'memory_usage': None,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def start_service(
        self, 
        host: str, 
        service_name: str
    ) -> bool:
        """Start service on remote host.
        
        Args:
            host: Remote host identifier
            service_name: Name of service to start
            
        Returns:
            True if started successfully, False otherwise
        """
        logger.info(f"Starting service '{service_name}' on {host}")
        
        try:
            # Execute systemctl start command
            command = f"sudo systemctl start {service_name}"
            stdout, stderr, exit_code = self._execute_remote_command(
                host, command
            )
            
            if exit_code != 0:
                logger.error(
                    f"Failed to start service '{service_name}': {stderr}"
                )
                return False
            
            # Verify service state
            if self._verify_service_state(host, service_name, 'running'):
                logger.info(
                    f"Successfully started service '{service_name}' on {host}"
                )
                return True
            else:
                logger.warning(
                    f"Service '{service_name}' start command succeeded but "
                    f"service is not running"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error starting service '{service_name}': {e}")
            return False
    
    def stop_service(
        self, 
        host: str, 
        service_name: str
    ) -> bool:
        """Stop service on remote host.
        
        Args:
            host: Remote host identifier
            service_name: Name of service to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        logger.info(f"Stopping service '{service_name}' on {host}")
        
        try:
            # Execute systemctl stop command
            command = f"sudo systemctl stop {service_name}"
            stdout, stderr, exit_code = self._execute_remote_command(
                host, command
            )
            
            if exit_code != 0:
                logger.error(
                    f"Failed to stop service '{service_name}': {stderr}"
                )
                return False
            
            # Verify service state
            if self._verify_service_state(host, service_name, 'stopped'):
                logger.info(
                    f"Successfully stopped service '{service_name}' on {host}"
                )
                return True
            else:
                logger.warning(
                    f"Service '{service_name}' stop command succeeded but "
                    f"service is still running"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error stopping service '{service_name}': {e}")
            return False
    
    def _execute_remote_command(
        self, 
        host: str, 
        command: str
    ) -> tuple:
        """Execute command on remote host.
        
        Args:
            host: Remote host identifier
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
            
        Raises:
            ConnectionError: If unable to connect
            TimeoutError: If command times out
            RemoteExecutionError: If execution fails
        """
        try:
            return self.ssh_manager.execute_command(host, command)
        except Exception as e:
            logger.error(f"Remote command execution failed: {e}")
            raise
    
    def _parse_service_status(
        self, 
        stdout: str, 
        stderr: str, 
        exit_code: int,
        service_name: str
    ) -> Dict[str, Any]:
        """Parse systemctl status output.
        
        Args:
            stdout: Command stdout
            stderr: Command stderr
            exit_code: Command exit code
            service_name: Name of the service
            
        Returns:
            Dictionary with parsed status information
        """
        status_dict = {
            'service_name': service_name,
            'status': 'unknown',
            'pid': None,
            'uptime': None,
            'memory_usage': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Determine status based on exit code and output
        if exit_code == 0:
            # Service is running
            if 'active (running)' in stdout.lower():
                status_dict['status'] = 'running'
            elif 'active (exited)' in stdout.lower():
                status_dict['status'] = 'stopped'
            elif 'inactive' in stdout.lower():
                status_dict['status'] = 'stopped'
        elif exit_code == 3:
            # Service is stopped
            status_dict['status'] = 'stopped'
        elif exit_code == 4:
            # Service not found
            status_dict['status'] = 'unknown'
        else:
            # Error or unknown state
            status_dict['status'] = 'error'
        
        # Extract PID if available
        pid_match = re.search(r'Main PID:\s+(\d+)', stdout)
        if pid_match:
            status_dict['pid'] = int(pid_match.group(1))
        
        # Extract uptime/active time
        uptime_match = re.search(
            r'Active:\s+active\s+\([^)]+\)\s+since\s+[^;]+;\s+([^;]+)',
            stdout
        )
        if uptime_match:
            status_dict['uptime'] = uptime_match.group(1).strip()
        
        # Extract memory usage if available
        memory_match = re.search(r'Memory:\s+([^\s]+)', stdout)
        if memory_match:
            status_dict['memory_usage'] = memory_match.group(1)
        
        return status_dict
    
    def _verify_service_state(
        self, 
        host: str, 
        service_name: str, 
        expected_state: str
    ) -> bool:
        """Verify service reached expected state.
        
        Args:
            host: Remote host identifier
            service_name: Name of service
            expected_state: Expected state ('running' or 'stopped')
            
        Returns:
            True if service is in expected state, False otherwise
        """
        try:
            status = self.check_service_status(host, service_name)
            
            if expected_state == 'running':
                return status['status'] == 'running'
            elif expected_state == 'stopped':
                return status['status'] in ['stopped', 'inactive']
            else:
                logger.warning(f"Unknown expected state: {expected_state}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying service state: {e}")
            return False
