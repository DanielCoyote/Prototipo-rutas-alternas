import { MapContainer, TileLayer } from "react-leaflet";

export default function MapView() {
  return (
    <div style={{ height: "100vh", width: "100%", background: "red" }}>
      <MapContainer
        center={[19.357, -99.064]}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  );
}
