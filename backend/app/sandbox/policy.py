"""Container runtime policy.

Non-root user, no Docker-socket exposure, no host bind mounts beyond the
single workspace volume, resource limits.
"""

from app.config import get_settings


def get_sandbox_policy(workspace_dir: str) -> dict:
    """Return the Docker container creation policy for a sandbox.

    Enforces resource limits, networking, and mount restrictions.
    """
    settings = get_settings()

    return {
        "image": settings.SANDBOX_IMAGE,
        "mem_limit": settings.SANDBOX_MEMORY_LIMIT,
        "nano_cpus": int(settings.SANDBOX_CPU_LIMIT * 1e9),  # Docker SDK expects nano cpus
        "network_disabled": False,  # True for strict, but might need pip install inside
        "read_only": False,  # Needs to write to /workspace
        "user": "sandbox",   # Must match the non-root user in Dockerfile.sandbox
        "working_dir": "/workspace",
        "volumes": {
            workspace_dir: {
                "bind": "/workspace",
                "mode": "rw"
            }
        },
        "detach": True,
        "tty": True,
        # Ensure the container stays alive in the background
        "command": ["sleep", "infinity"],
        # Seccomp and apparmor can be added here for production hardening
        "security_opt": ["no-new-privileges:true"],
    }
