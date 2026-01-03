import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..core.config import supabase
from .auth import get_current_user

logger = logging.getLogger("backend.favorites")

router = APIRouter()

class FavoritePlace(BaseModel):
    label: str
    latitude: float
    longitude: float

class FavoritePlaceResponse(BaseModel):
    id: str
    user_id: str
    label: str
    latitude: float
    longitude: float
    created_at: str

@router.get("/favorites", response_model=List[FavoritePlaceResponse])
async def get_favorites(current_user: dict = Depends(get_current_user)):
    """
    Get all favorite places for the current user.
    """
    try:
        user_id = current_user["user_id"]
        
        response = supabase.table("favorite_places") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
        
        return response.data
    except Exception as e:
        logger.error(f"Error fetching favorites: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener lugares favoritos")

@router.post("/favorites", response_model=FavoritePlaceResponse)
async def create_favorite(
    favorite: FavoritePlace,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new favorite place for the current user.
    """
    try:
        user_id = current_user["user_id"]
        
        response = supabase.table("favorite_places") \
            .insert({
                "user_id": user_id,
                "label": favorite.label,
                "latitude": favorite.latitude,
                "longitude": favorite.longitude
            }) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Error al crear lugar favorito")
        
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating favorite: {e}")
        raise HTTPException(status_code=500, detail="Error al crear lugar favorito")

@router.delete("/favorites/{favorite_id}")
async def delete_favorite(
    favorite_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a favorite place. Only the owner can delete it.
    """
    try:
        user_id = current_user["user_id"]
        
        # Verify ownership
        existing = supabase.table("favorite_places") \
            .select("user_id") \
            .eq("id", favorite_id) \
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Lugar favorito no encontrado")
        
        if existing.data[0]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este favorito")
        
        # Delete
        supabase.table("favorite_places") \
            .delete() \
            .eq("id", favorite_id) \
            .execute()
        
        return {"message": "Lugar favorito eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting favorite: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar lugar favorito")
