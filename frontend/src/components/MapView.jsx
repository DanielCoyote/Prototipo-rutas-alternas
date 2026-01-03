import "leaflet-defaulticon-compatibility";
import "leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import { useEffect } from "react";
import PolygonsLayer from "./PolygonsLayer";

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

export default function MapView({ origin, destination, route }) {
  return (
    <div style={{ height: "100vh", width: "100%" }}>
      <MapContainer
        center={[19.357, -99.064]}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <PolygonsLayer styleOptions={{ fillColor: undefined }} />

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


    </div>
  );
}
