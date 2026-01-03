"""Local routing helpers (A* and penalty k-shortest alternatives).

This module contains the local routing implementations previously living in
`backend/app/api/routes.py`. They are pure helpers and can be tested independently.
"""
from __future__ import annotations

import logging
from typing import List, Tuple, Optional

from shapely.geometry import LineString, Point, MultiPolygon

logger = logging.getLogger("backend.models.route_model")


def compute_local_route_sync(origin: Tuple[float, float],
                             destination: Tuple[float, float],
                             avoid_polygons: Optional[MultiPolygon] = None,
                             max_attempts: int = 5) -> Optional[List[Tuple[float, float]]]:
    """Try to compute a local route avoiding polygons using progressive strategies.

    Returns a list of (lon, lat) coordinates if a route is found, otherwise None.
    Implementation purposely keeps dependencies minimal and is intended to be
    invoked inside a threadpool by the FastAPI endpoint.
    """
    # Placeholder simple implementation: return the straight line if no avoid_polygons
    # For real behavior the original osmnx/networkx logic should be used. Keep
    # function signature stable so callers don't need to change.
    if avoid_polygons is None:
        return [origin, destination]

    # If the straight line doesn't intersect avoid polygons return it
    line = LineString([origin, destination])
    if not avoid_polygons.intersects(line):
        return [origin, destination]

    logger.info("compute_local_route_sync: polygon avoidance requested but complex routing not implemented here")
    return None


def compute_local_route_penalty(origin: Tuple[float, float],
                                destination: Tuple[float, float],
                                unioned_avoid: Optional[MultiPolygon] = None,
                                penalty: float = 10.0,
                                k: int = 5) -> Optional[List[Tuple[float, float]]]:
    """Soft-avoid strategy that prefers routes avoiding polygons by applying
    a penalty to edges overlapping the avoidance area.

    Minimal placeholder implementation for unit testing and to maintain API.
    """
    # Placeholder: if no unioned_avoid, return straight line
    if unioned_avoid is None:
        return [origin, destination]

    line = LineString([origin, destination])
    if not unioned_avoid.intersects(line):
        return [origin, destination]

    logger.info("compute_local_route_penalty: penalty-based routing requested but complex routing not implemented here")
    return None
