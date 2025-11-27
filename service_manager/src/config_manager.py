"""Configuration Manager for Service Fleet Manager.

This module handles configuration generation from templates, validation,
and deployment to remote hosts.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from fabric import Connection

from service_manager.src.utils.validators import validate_config_schema


logger = logging.getLogger(__name__)


class TemplateNotFoundError(Exception):
    """Exception raised when a template file is not found."""
    pass


class TemplateRenderError(Exception):
    """Exception raised when template rendering fails."""
    pass


class ConfigurationManager:
    """Manages configuration generation, validation, and deployment.
    
    This class handles loading Jinja2 templates, rendering them with parameters,
    validating the generated configurations, and deploying them to remote hosts.
    """
    
    def __init__(self, template_dir: str, config_dir: str):
        """Initialize ConfigurationManager.
        
        Args:
            template_dir: Directory containing Jinja2 templates
            config_dir: Directory for storing generated configurations
        """
        self.template_dir = Path(template_dir)
        self.config_dir = Path(config_dir)
        
        # Create directories if they don't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False
        )
        
        logger.info(
            f"ConfigurationManager initialized with template_dir={template_dir}, "
            f"config_dir={config_dir}"
        )
    
    def generate_config(
        self, 
        template_name: str, 
        env: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate configuration from template.
        
        Args:
            template_name: Name of template file (without extension)
            env: Environment identifier (dev/prod)
            params: Dictionary of template parameters
            
        Returns:
            Generated configuration as dictionary
            
        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateRenderError: If template rendering fails
        """
        logger.info(
            f"Generating config from template={template_name}, env={env}"
        )
        
        try:
            # Load template
            template = self._load_template(template_name)
            
            # Add environment to params
            params_with_env = {**params, 'env': env}
            
            # Render template
            rendered = self._render_template(template, params_with_env)
            
            # Parse JSON
            config = json.loads(rendered)
            
            logger.info(f"Successfully generated config for {template_name}")
            return config
            
        except TemplateNotFound as e:
            error_msg = f"Template '{template_name}' not found in {self.template_dir}"
            logger.error(error_msg)
            raise TemplateNotFoundError(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse rendered template as JSON: {e}"
            logger.error(error_msg)
            raise TemplateRenderError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to render template '{template_name}': {e}"
            logger.error(error_msg)
            raise TemplateRenderError(error_msg) from e
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating configuration")
        
        try:
            is_valid, errors = validate_config_schema(config)
            
            if not is_valid:
                logger.warning(f"Configuration validation failed: {errors}")
            else:
                logger.info("Configuration validation passed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False
    
    def deploy_config(
        self, 
        config: Dict[str, Any], 
        target_host: str, 
        target_path: str
    ) -> bool:
        """Deploy configuration to remote host.
        
        Args:
            config: Configuration dictionary
            target_host: Remote host identifier
            target_path: Path on remote host
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to host
            PermissionError: If insufficient permissions
        """
        logger.info(
            f"Deploying config to host={target_host}, path={target_path}"
        )
        
        try:
            # Save config locally first
            local_path = self.config_dir / f"temp_{target_host}_config.json"
            self._save_config_local(config, str(local_path))
            
            # Connect to remote host and transfer file
            conn = Connection(target_host)
            
            # Ensure remote directory exists
            remote_dir = os.path.dirname(target_path)
            if remote_dir:
                conn.run(f"mkdir -p {remote_dir}", hide=True)
            
            # Transfer file
            conn.put(str(local_path), target_path)
            
            # Clean up local temp file
            local_path.unlink()
            
            logger.info(f"Successfully deployed config to {target_host}:{target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy config to {target_host}: {e}")
            
            # Clean up temp file if it exists
            if 'local_path' in locals() and local_path.exists():
                local_path.unlink()
            
            return False
    
    def _load_template(self, template_name: str) -> Template:
        """Load Jinja2 template.
        
        Args:
            template_name: Name of template file
            
        Returns:
            Loaded Jinja2 Template object
            
        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        # Add .json extension if not present
        if not template_name.endswith('.json'):
            template_name = f"{template_name}.json"
        
        logger.debug(f"Loading template: {template_name}")
        return self.jinja_env.get_template(template_name)
    
    def _render_template(self, template: Template, params: Dict[str, Any]) -> str:
        """Render template with parameters.
        
        Args:
            template: Jinja2 Template object
            params: Dictionary of template parameters
            
        Returns:
            Rendered template as string
        """
        logger.debug(f"Rendering template with params: {list(params.keys())}")
        return template.render(**params)
    
    def _save_config_local(self, config: Dict[str, Any], path: str) -> None:
        """Save configuration to local filesystem.
        
        Args:
            config: Configuration dictionary
            path: Local file path
        """
        logger.debug(f"Saving config to local path: {path}")
        
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(path, 0o600)
