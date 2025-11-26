"""SSH connection management"""

import logging
import time
from typing import Dict, Optional
from fabric import Connection
from paramiko.ssh_exception import SSHException, NoValidConnectionsError, AuthenticationException


logger = logging.getLogger(__name__)


class SSHConnectionManager:
    """Manages SSH connections with connection pooling and retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30
    ):
        """
        Initialize SSH connection manager.
        
        Args:
            max_retries: Maximum number of connection retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            timeout: Default timeout for operations in seconds
        """
        self._connections: Dict[str, Connection] = {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        logger.info("SSHConnectionManager initialized")
    
    def get_connection(self, host: str) -> Connection:
        """
        Get or create SSH connection with retry logic.
        
        Args:
            host: Remote host identifier (hostname or user@hostname)
            
        Returns:
            Active SSH connection
            
        Raises:
            ConnectionError: If unable to establish connection after retries
            AuthenticationException: If authentication fails
        """
        if host in self._connections:
            conn = self._connections[host]
            # Test if connection is still alive
            try:
                conn.run('echo test', hide=True, timeout=5)
                logger.debug(f"Reusing existing connection to {host}")
                return conn
            except Exception as e:
                logger.warning(f"Existing connection to {host} is dead: {e}")
                self.close_connection(host)
        
        # Create new connection with retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to connect to {host} (attempt {attempt + 1}/{self.max_retries})")
                conn = Connection(
                    host,
                    connect_timeout=self.timeout,
                    connect_kwargs={"timeout": self.timeout}
                )
                # Test connection
                conn.open()
                self._connections[host] = conn
                logger.info(f"Successfully connected to {host}")
                return conn
            
            except AuthenticationException as e:
                logger.error(f"Authentication failed for {host}: {e}")
                raise
            
            except (SSHException, NoValidConnectionsError, OSError) as e:
                logger.warning(f"Connection attempt {attempt + 1} failed for {host}: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_msg = f"Failed to connect to {host} after {self.max_retries} attempts"
                    logger.error(error_msg)
                    raise ConnectionError(error_msg) from e
        
        raise ConnectionError(f"Failed to connect to {host}")
    
    def close_connection(self, host: str) -> None:
        """
        Close SSH connection for a specific host.
        
        Args:
            host: Remote host identifier
        """
        if host in self._connections:
            try:
                self._connections[host].close()
                logger.info(f"Closed connection to {host}")
            except Exception as e:
                logger.warning(f"Error closing connection to {host}: {e}")
            finally:
                del self._connections[host]
    
    def close_all_connections(self) -> None:
        """Close all active SSH connections."""
        hosts = list(self._connections.keys())
        for host in hosts:
            self.close_connection(host)
        logger.info("All connections closed")
    
    def execute_command(
        self,
        host: str,
        command: str,
        timeout: Optional[int] = None
    ) -> tuple:
        """
        Execute command on remote host with retry logic and timeout handling.
        
        Args:
            host: Remote host identifier
            command: Command to execute
            timeout: Command timeout in seconds (uses default if None)
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
            
        Raises:
            ConnectionError: If unable to connect to host
            TimeoutError: If command execution times out
            RemoteExecutionError: If command execution fails
        """
        timeout = timeout or self.timeout
        
        for attempt in range(self.max_retries):
            try:
                conn = self.get_connection(host)
                logger.info(f"Executing command on {host}: {command}")
                
                result = conn.run(
                    command,
                    hide=True,
                    warn=True,
                    timeout=timeout
                )
                
                logger.debug(f"Command completed with exit code {result.exited}")
                return (result.stdout.strip(), result.stderr.strip(), result.exited)
            
            except TimeoutError as e:
                logger.error(f"Command timed out on {host} after {timeout}s: {command}")
                raise
            
            except (SSHException, OSError) as e:
                logger.warning(f"Execution attempt {attempt + 1} failed on {host}: {e}")
                
                # Close the bad connection
                self.close_connection(host)
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_msg = f"Failed to execute command on {host} after {self.max_retries} attempts"
                    logger.error(error_msg)
                    raise ConnectionError(error_msg) from e
            
            except Exception as e:
                logger.error(f"Unexpected error executing command on {host}: {e}")
                raise RemoteExecutionError(f"Command execution failed: {e}") from e
        
        raise ConnectionError(f"Failed to execute command on {host}")


class RemoteExecutionError(Exception):
    """Exception raised when remote command execution fails."""
    pass
