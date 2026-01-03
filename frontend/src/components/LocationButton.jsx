import { useMap } from "react-leaflet";
import { useEffect, useState } from "react";
import L from "leaflet";

export default function LocationButton() {
  const map = useMap();
  const [userLocation, setUserLocation] = useState(null);
  const [marker, setMarker] = useState(null);

  useEffect(() => {
    // Crear el control personalizado
    const LocationControl = L.Control.extend({
      onAdd: function() {
        const btn = L.DomUtil.create('button', 'location-button');
        btn.innerHTML = '📍';
        btn.title = 'Ver mi ubicación';
        
        btn.onclick = function(e) {
          L.DomEvent.stopPropagation(e);
          L.DomEvent.preventDefault(e);
          
          if ("geolocation" in navigator) {
            btn.innerHTML = '⏳';
            btn.disabled = true;
            
            navigator.geolocation.getCurrentPosition(
              (position) => {
                const { latitude, longitude } = position.coords;
                const location = [latitude, longitude];
                
                setUserLocation(location);
                map.setView(location, 16);
                
                // Crear o actualizar marcador
                if (marker) {
                  marker.setLatLng(location);
                } else {
                  const newMarker = L.marker(location, {
                    icon: L.icon({
                      iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="8" fill="#4FD1C5" stroke="white" stroke-width="2"/>
                          <circle cx="12" cy="12" r="3" fill="white"/>
                        </svg>
                      `),
                      iconSize: [32, 32],
                      iconAnchor: [16, 16]
                    })
                  }).addTo(map);
                  
                  newMarker.bindPopup("Tu ubicación actual");
                  setMarker(newMarker);
                }
                
                btn.innerHTML = '📍';
                btn.disabled = false;
              },
              (error) => {
                console.error("Error obteniendo ubicación:", error);
                alert("No se pudo obtener tu ubicación. Verifica los permisos del navegador.");
                btn.innerHTML = '📍';
                btn.disabled = false;
              },
              {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
              }
            );
          } else {
            alert("Tu navegador no soporta geolocalización");
          }
        };
        
        return btn;
      }
    });

    const locationControl = new LocationControl({ position: 'bottomright' });
    locationControl.addTo(map);

    return () => {
      map.removeControl(locationControl);
      if (marker) {
        map.removeLayer(marker);
      }
    };
  }, [map, marker]);

  return null;
}
