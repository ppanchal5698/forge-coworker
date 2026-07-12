"""Terminal MCP server.

Wraps Python's subprocess to run bash commands inside the sandbox container
only, capturing output and enforcing the retry/error-count contract.
Runs inside the sandbox container.
"""

import asyncio

from mcp.server.fastmcp import FastMCP

# The sandbox mounts the workspace at /workspace
WORKSPACE_DIR = "/workspace"

mcp = FastMCP("terminal")


@mcp.tool()
async def execute_command(command: str) -> str:
    """Execute a bash command in the workspace directory and return the output.
    
    Args:
        command: The bash command to run (e.g., 'ls -la', 'python script.py').
    """
    try:
        # Use asyncio subprocess to avoid blocking the MCP event loop
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE_DIR,
        )
        
        stdout, stderr = await process.communicate()
        
        out = stdout.decode("utf-8").strip()
        err = stderr.decode("utf-8").strip()
        
        result = []
        if process.returncode != 0:
            result.append(f"Command failed with exit code {process.returncode}")
        
        if out:
            result.append(f"STDOUT:\n{out}")
        if err:
            result.append(f"STDERR:\n{err}")
            
        if not result:
            return "Command executed successfully (no output)."
            
        return "\n\n".join(result)
        
    except Exception as e:
        return f"Error executing command: {str(e)}"


if __name__ == "__main__":
    mcp.run()
