"""Validation utilities for configuration, hosts, and service names."""

import logging
import re
import socket
from typing import Tuple, List


logger = logging.getLogger(__name__)


def validate_config_schema(config: dict) -> Tuple[bool, List[str]]:
    """
    Validate configuration against expected schema.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(config, dict):
        errors.append("Configuration must be a dictionary")
        return False, errors
    
    # Check for required top-level 'service' key
    if 'service' not in config:
        errors.append("Configuration must contain 'service' key")
        return False, errors
    
    service = config['service']
    if not isinstance(service, dict):
        errors.append("'service' must be a dictionary")
        return False, errors
    
    # Required fields in service configuration
    required_fields = {
        'name': str,
        'version': str,
        'env': str,
        'port': int
    }
    
    for field, expected_type in required_fields.items():
        if field not in service:
            errors.append(f"Missing required field: service.{field}")
        elif not isinstance(service[field], expected_type):
            errors.append(
                f"Field 'service.{field}' must be of type {expected_type.__name__}, "
                f"got {type(service[field]).__name__}"
            )
    
    # Validate environment value
    if 'env' in service and service['env'] not in ['dev', 'prod']:
        errors.append("Field 'service.env' must be either 'dev' or 'prod'")
    
    # Validate port range
    if 'port' in service and isinstance(service['port'], int):
        if not (1 <= service['port'] <= 65535):
            errors.append("Field 'service.port' must be between 1 and 65535")
    
    # Optional fields validation
    if 'max_memory' in service and not isinstance(service['max_memory'], str):
        errors.append("Field 'service.max_memory' must be a string")
    
    # Validate healthcheck if present
    if 'healthcheck' in service:
        healthcheck = service['healthcheck']
        if not isinstance(healthcheck, dict):
            errors.append("Field 'service.healthcheck' must be a dictionary")
        else:
            healthcheck_fields = {
                'endpoint': str,
                'interval': str,
                'timeout': str
            }
            for field, expected_type in healthcheck_fields.items():
                if field not in healthcheck:
                    errors.append(f"Missing required field: service.healthcheck.{field}")
                elif not isinstance(healthcheck[field], expected_type):
                    errors.append(
                        f"Field 'service.healthcheck.{field}' must be of type {expected_type.__name__}"
                    )
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info("Configuration validation passed")
    else:
        logger.warning(f"Configuration validation failed with {len(errors)} error(s)")
        for error in errors:
            logger.debug(f"Validation error: {error}")
    
    return is_valid, errors


def validate_host_reachable(host: str, timeout: int = 5) -> bool:
    """
    Check if host is reachable via network.
    
    Args:
        host: Hostname or IP address (can include user@ prefix)
        timeout: Connection timeout in seconds
        
    Returns:
        True if host is reachable, False otherwise
    """
    # Extract hostname if user@host format
    hostname = host.split('@')[-1]
    
    # Extract hostname if port is specified
    hostname = hostname.split(':')[0]
    
    try:
        logger.debug(f"Checking if host {hostname} is reachable")
        
        # Try to resolve hostname
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(hostname)
        
        # Try to connect to SSH port (22)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((hostname, 22))
        sock.close()
        
        if result == 0:
            logger.info(f"Host {hostname} is reachable")
            return True
        else:
            logger.warning(f"Host {hostname} is not reachable on port 22")
            return False
    
    except socket.gaierror as e:
        logger.warning(f"Failed to resolve hostname {hostname}: {e}")
        return False
    
    except socket.timeout:
        logger.warning(f"Connection to {hostname} timed out")
        return False
    
    except Exception as e:
        logger.warning(f"Error checking host {hostname} reachability: {e}")
        return False


def validate_service_name(service_name: str) -> bool:
    """
    Validate service name format.
    
    Service names should:
    - Be 1-64 characters long
    - Contain only alphanumeric characters, hyphens, and underscores
    - Start with an alphanumeric character
    - Not end with a hyphen or underscore
    
    Args:
        service_name: Service name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not service_name:
        logger.warning("Service name cannot be empty")
        return False
    
    if not isinstance(service_name, str):
        logger.warning(f"Service name must be a string, got {type(service_name).__name__}")
        return False
    
    # Check length
    if not (1 <= len(service_name) <= 64):
        logger.warning(f"Service name must be 1-64 characters long, got {len(service_name)}")
        return False
    
    # Check format: alphanumeric, hyphens, underscores
    # Must start with alphanumeric, not end with hyphen or underscore
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$'
    
    if not re.match(pattern, service_name):
        logger.warning(
            f"Service name '{service_name}' has invalid format. "
            "Must contain only alphanumeric characters, hyphens, and underscores, "
            "start with alphanumeric, and not end with hyphen or underscore"
        )
        return False
    
    logger.debug(f"Service name '{service_name}' is valid")
    return True
