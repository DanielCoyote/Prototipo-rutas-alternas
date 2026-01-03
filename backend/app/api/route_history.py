import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..core.config import supabase
from .auth import get_current_user

logger = logging.getLogger("backend.route_history")

router = APIRouter()

class RouteHistoryCreate(BaseModel):
    origin_label: str
    destination_label: str
    origin_coords: List[float]  # [lon, lat]
    destination_coords: List[float]  # [lon, lat]
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None

class RouteHistoryResponse(BaseModel):
    id: str
    user_id: str
    origin_label: str
    destination_label: str
    origin_coords: List[float]
    destination_coords: List[float]
    duration_minutes: Optional[float]
    distance_km: Optional[float]
    created_at: str

@router.get("/route/history", response_model=List[RouteHistoryResponse])
async def get_route_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get route history for the current user.
    Returns the most recent routes (default 10).
    """
    try:
        user_id = current_user["user_id"]
        
        response = supabase.table("route_history") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        return response.data
    except Exception as e:
        logger.error(f"Error fetching route history: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener historial de rutas")

@router.post("/route/history", response_model=RouteHistoryResponse)
async def create_route_history(
    route: RouteHistoryCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Save a route to history.
    """
    try:
        user_id = current_user["user_id"]
        
        response = supabase.table("route_history") \
            .insert({
                "user_id": user_id,
                "origin_label": route.origin_label,
                "destination_label": route.destination_label,
                "origin_coords": route.origin_coords,
                "destination_coords": route.destination_coords,
                "duration_minutes": route.duration_minutes,
                "distance_km": route.distance_km
            }) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Error al guardar ruta en historial")
        
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating route history: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar ruta en historial")

@router.delete("/route/history/{route_id}")
async def delete_route_history(
    route_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a route from history. Only the owner can delete it.
    """
    try:
        user_id = current_user["user_id"]
        
        # Verify ownership
        existing = supabase.table("route_history") \
            .select("user_id") \
            .eq("id", route_id) \
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Ruta no encontrada")
        
        if existing.data[0]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta ruta")
        
        # Delete
        supabase.table("route_history") \
            .delete() \
            .eq("id", route_id) \
            .execute()
        
        return {"message": "Ruta eliminada del historial"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting route history: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar ruta del historial")
