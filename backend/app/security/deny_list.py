"""Deny list.

Hard, pattern-based deny-list of destructive commands/paths (e.g. rm -rf,
DROP TABLE, force-push), enforced independently of model judgement per the
Risk #1 mitigation in the PRD.
"""

import re

# Regex patterns for highly destructive terminal commands
DESTRUCTIVE_COMMAND_PATTERNS = [
    r"rm\s+-r[fF]?",        # Recursive delete
    r">\s*/dev/null",       # Redirection to null (often used to hide errors from destructive commands)
    r"dd\s+if=",            # dd command which can overwrite disks (though sandbox restricts block devices, still good practice)
    r"mkfs",                # Format filesystem
    r"chmod\s+-R\s+777",    # Recursive permissive chmod
    r"chown\s+-R",          # Recursive chown
    r"git\s+push\s+.*--force", # Force push
    r"git\s+reset\s+--hard",   # Hard reset
    r"curl\s+.*\|\s*bash",  # Pipe to bash
    r"wget\s+.*\|\s*bash",  # Pipe to bash
]

# Regex patterns for destructive SQL or database commands if passed via terminal tools
DESTRUCTIVE_SQL_PATTERNS = [
    r"(?i)\bDROP\s+TABLE\b",
    r"(?i)\bDROP\s+DATABASE\b",
    r"(?i)\bTRUNCATE\s+TABLE\b",
    r"(?i)\bALTER\s+TABLE\s+.*DROP\b",
]

COMPILED_PATTERNS = [re.compile(p) for p in DESTRUCTIVE_COMMAND_PATTERNS + DESTRUCTIVE_SQL_PATTERNS]


def is_hard_denied(command: str) -> bool:
    """Check if a command matches any hard-coded destructive patterns.
    
    Args:
        command: The terminal command or query to check.
        
    Returns:
        True if the command matches a deny-list pattern, False otherwise.
    """
    for pattern in COMPILED_PATTERNS:
        if pattern.search(command):
            return True
    return False
