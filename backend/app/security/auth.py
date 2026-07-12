"""Auth module.

Single-operator bearer-token check protecting the API and dashboard, since
the system still runs a local HTTP server reachable on the LAN.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

bearer_scheme = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Verify the provided bearer token matches the API_BEARER_TOKEN setting."""
    settings = get_settings()
    
    # Simple check for single-operator local deploy
    if credentials.credentials != settings.API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return credentials.credentials
