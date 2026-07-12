"""Docker sandbox manager.

Spins up and tears down the per-workspace Docker container, mounting only that
workspace's directory as a volume — the hard security boundary from PRD
Section 7.10.
"""

import docker
from docker.models.containers import Container
from structlog import get_logger

from app.config import get_settings
from app.sandbox.policy import get_sandbox_policy

logger = get_logger(__name__)


class SandboxManager:
    """Manages the lifecycle of Docker sandbox containers for workspaces."""

    def __init__(self):
        self.client = docker.from_env()

    def _get_container_name(self, workspace_id: str) -> str:
        """Return the predictable container name for a workspace."""
        return f"forge-sandbox-{workspace_id}"

    def ensure_sandbox(self, workspace_id: str, workspace_dir: str) -> str:
        """Ensure the sandbox container is running for the workspace.

        Returns the container name, which can be used by `docker exec`.
        """
        container_name = self._get_container_name(workspace_id)
        
        try:
            container = self.client.containers.get(container_name)
            if container.status != "running":
                logger.info(f"Starting stopped sandbox {container_name}")
                container.start()
            return container_name
        except docker.errors.NotFound:
            # Container doesn't exist, create it
            logger.info(f"Creating new sandbox {container_name}")
            policy = get_sandbox_policy(workspace_dir)
            
            # Add container name to policy
            policy["name"] = container_name
            
            try:
                container = self.client.containers.run(**policy)
                return container_name
            except Exception as e:
                logger.error(f"Failed to create sandbox: {str(e)}")
                raise

    def stop_sandbox(self, workspace_id: str) -> None:
        """Stop and remove a sandbox container."""
        container_name = self._get_container_name(workspace_id)
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=2)
            container.remove(force=True)
            logger.info(f"Stopped and removed sandbox {container_name}")
        except docker.errors.NotFound:
            pass


# Singleton instance
sandbox_manager = SandboxManager()
