import MapView from "../components/MapView";
import SearchBar from "../components/SearchBar/SearchBar";

export default function Home() {

  const handleSearch = (origin, destination) => {
    console.log("Buscar ruta:", origin, "→", destination);
    // aquí luego llamaremos al backend FastAPI
  };

  return (
    <div style={{ height: "100vh", width: "100%", position: "relative" }}>
      <SearchBar onSearch={handleSearch} />
      <MapView />
    </div>
  );
}
