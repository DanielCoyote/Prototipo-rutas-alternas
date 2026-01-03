import "leaflet-defaulticon-compatibility";
import "leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css";
import "leaflet/dist/leaflet.css";
import "../styles/map-controls.css";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, ZoomControl } from "react-leaflet";
import { useEffect, useState } from "react";
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button } from "@mui/material";
import PolygonsLayer from "./PolygonsLayer";
import FavoriteMarkers from "./FavoriteMarkers";
import LocationButton from "./LocationButton";
import { createFavorite } from "../services/api";

function FitBounds({ route, origin, destination }) {
  const map = useMap();

  useEffect(() => {
    const pts = [];
    if (route && route.length) pts.push(...route);
    if (origin) pts.push(origin);
    if (destination) pts.push(destination);

    if (pts.length === 0) return;

    const bounds = pts.map(p => [p[0], p[1]]);
    map.fitBounds(bounds, { padding: [50, 50] });
  }, [map, route, origin, destination]);

  return null;
}

// Component to handle map double clicks
function MapClickHandler({ onClick }) {
  const map = useMap();

  useEffect(() => {
    map.on('dblclick', onClick);
    return () => {
      map.off('dblclick', onClick);
    };
  }, [map, onClick]);

  return null;
}

export default function MapView({ origin, destination, route, onDestinationChange }) {
  const [openDialog, setOpenDialog] = useState(false);
  const [favoriteLabel, setFavoriteLabel] = useState("");
  const [clickedLocation, setClickedLocation] = useState(null);
  const [favoritesKey, setFavoritesKey] = useState(0);

  const handleMapClick = (e) => {
    setClickedLocation([e.latlng.lat, e.latlng.lng]);
    setOpenDialog(true);
  };

  const handleSaveFavorite = async () => {
    if (!favoriteLabel.trim()) {
      alert("Por favor ingresa un nombre para el lugar");
      return;
    }

    try {
      await createFavorite(favoriteLabel, clickedLocation[0], clickedLocation[1]);
      setOpenDialog(false);
      setFavoriteLabel("");
      setClickedLocation(null);
      // Refresh favorites by changing key
      setFavoritesKey(prev => prev + 1);
    } catch (error) {
      console.error("Error guardando favorito:", error);
      alert("Error al guardar el favorito: " + error.message);
    }
  };

  const handleFavoriteClick = (coords, label) => {
    if (onDestinationChange) {
      onDestinationChange(coords, label);
    }
  };

  return (
    <div style={{ height: "100vh", width: "100%", position: "relative" }}>
      <MapContainer
        center={[19.357, -99.064]}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
      >
        <ZoomControl position="bottomright" />
        <LocationButton />
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <PolygonsLayer styleOptions={{ fillColor: undefined }} />
        <FavoriteMarkers key={favoritesKey} onFavoriteClick={handleFavoriteClick} />

        <MapClickHandler onClick={handleMapClick} />

        {origin && (
          <Marker position={origin}>
            <Popup>Origen</Popup>
          </Marker>
        )}

        {destination && (
          <Marker position={destination}>
            <Popup>Destino</Popup>
          </Marker>
        )}

        {route && route.length > 0 && (
          <Polyline positions={route} />
        )}

        <FitBounds route={route} origin={origin} destination={destination} />
      </MapContainer>

      {/* Dialog for adding favorite */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Agregar Lugar Favorito</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nombre del lugar"
            type="text"
            fullWidth
            variant="outlined"
            value={favoriteLabel}
            onChange={(e) => setFavoriteLabel(e.target.value)}
            placeholder="Ej: Casa, Trabajo, Escuela..."
          />
          {clickedLocation && (
            <p style={{ color: "#666", fontSize: "14px", marginTop: "10px" }}>
              Coordenadas: {clickedLocation[0].toFixed(5)}, {clickedLocation[1].toFixed(5)}
            </p>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)} color="inherit">
            Cancelar
          </Button>
          <Button onClick={handleSaveFavorite} variant="contained" style={{ backgroundColor: "#4FD1C5" }}>
            Guardar
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}
