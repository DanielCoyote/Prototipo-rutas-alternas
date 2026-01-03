import logging
import os
import httpx
from fastapi import HTTPException

logger = logging.getLogger("backend.api.route")

ORS_KEY = os.getenv("ORS_API_KEY")


async def call_ors_directions(url, body, timeout=20):
    """Call ORS directions endpoint and return the httpx Response."""
    if not ORS_KEY:
        logger.error("ORS_API_KEY not configured when calling ORS directions")
        raise HTTPException(status_code=500, detail="ORS_API_KEY not configured on server")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(url, json=body)
            return r
        except httpx.HTTPError as e:
            logger.exception("Network error when calling ORS directions")
            raise HTTPException(status_code=502, detail=f"Network error when contacting ORS: {str(e)}")
