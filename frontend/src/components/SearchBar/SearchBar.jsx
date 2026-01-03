import "./SearchBar.css";
import { useState, useEffect, useRef } from "react";
import { autocomplete } from "../../services/ors";
import { useNavigate } from "react-router-dom";
import RouteHistory from "../RouteHistory";

export default function SearchBar({ onSearch, onLogout, externalDestination, onRouteFromHistory, avoidZones, setAvoidZones }) {
  const navigate = useNavigate();
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const [originCoords, setOriginCoords] = useState(null);
  const [destinationCoords, setDestinationCoords] = useState(null);

  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [autocompleteError, setAutocompleteError] = useState(null);

  const [activeField, setActiveField] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuView, setMenuView] = useState("main"); // "main" | "history"

  const debounceTimerRef = useRef(null);

  const handleAutocomplete = async (value, field) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (!value || value.trim().length < 3) {
      if (field === "origin") {
        setOriginSuggestions([]);
      } else {
        setDestinationSuggestions([]);
      }
      return;
    }

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const results = await autocomplete(value);
        setAutocompleteError(null);
        if (field === "origin") {
          setOriginSuggestions(results);
        } else {
          setDestinationSuggestions(results);
        }
      } catch (error) {
        console.error(`Error fetching ${field} suggestions:`, error);
        setTimeout(() => setAutocompleteError(null), 3000);
        if (field === "origin") {
          setOriginSuggestions([]);
        } else {
          setDestinationSuggestions([]);
        }
      }
    }, 500);
  };

  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (externalDestination) {
      setDestination(externalDestination.label);
      setDestinationCoords(externalDestination.coords);
    }
  }, [externalDestination]);

  const selectSuggestion = (item, field) => {
    if (field === "origin") {
      setOrigin(item.label);
      setOriginCoords(item.coords);
      setOriginSuggestions([]);
      setActiveField(null);
    } else {
      setDestination(item.label);
      setDestinationCoords(item.coords);
      setDestinationSuggestions([]);
      setActiveField(null);
    }
  };

  const handleSearchClick = () => {
    if (!originCoords || !destinationCoords) return;
    onSearch({ label: origin, coords: originCoords }, { label: destination, coords: destinationCoords });
  };

  const onKeyDownDestination = (e) => {
    if (e.key === "Enter") {
      handleSearchClick();
    }
  };

  const handleRouteSelect = (routeData) => {
    setOrigin(routeData.origin.label);
    setOriginCoords(routeData.origin.coords);
    setDestination(routeData.destination.label);
    setDestinationCoords(routeData.destination.coords);
    setMenuOpen(false);
    setMenuView("main");
    
    if (onRouteFromHistory) {
      onRouteFromHistory(routeData.origin, routeData.destination);
    }
  };

  return (
    <div className="search-container" style={{ width: "400px" }}>
      <div className="search-header" style={{ display: 'flex', gap: 10, alignItems: 'center', padding: "12px 16px" }}>
        <button 
          className="menu-btn"
          onClick={() => setMenuOpen(!menuOpen)}
          style={{
            background: menuOpen ? "#4FD1C5" : "transparent",
            color: menuOpen ? "white" : "#2D3748",
            border: "none",
            fontSize: "24px",
            cursor: "pointer",
            padding: "4px 8px",
            borderRadius: "4px",
            transition: "all 0.3s"
          }}
        >
          ☰
        </button>
        <h2 style={{ margin: 0, fontSize: "18px", color: "#2D3748" }}>Direcciones de Viaje</h2>
      </div>

      {/* Checkbox para evitar zonas de riesgo */}
      <div style={{ padding: "8px 16px", backgroundColor: "#F7FAFC", borderBottom: "1px solid #E2E8F0" }}>
        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: "14px", color: "#2D3748" }}>
          <input
            type="checkbox"
            checked={avoidZones}
            onChange={(e) => setAvoidZones(e.target.checked)}
            style={{ marginRight: "8px", width: "16px", height: "16px", cursor: "pointer" }}
          />
          <span style={{ fontWeight: "500" }}>🚫 Evitar zonas de riesgo inundables</span>
        </label>
      </div>

      {/* Menu desplegable animado */}
      <div style={{
        maxHeight: menuOpen ? "500px" : "0",
        overflow: "hidden",
        transition: "max-height 0.3s ease-in-out",
        backgroundColor: "#F7FAFC",
        borderRadius: menuOpen ? "0 0 8px 8px" : "0"
      }}>
        {menuView === "main" && (
          <div style={{ padding: "16px" }}>
            <button
              onClick={() => setMenuView("history")}
              style={{
                width: "100%",
                padding: "12px",
                marginBottom: "8px",
                backgroundColor: "white",
                border: "1px solid #E2E8F0",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "500",
                color: "#2D3748",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}
            >
              📜 Historial de Rutas
            </button>
            <button
              onClick={() => navigate("/usuarios")}
              style={{
                width: "100%",
                padding: "12px",
                marginBottom: "8px",
                backgroundColor: "white",
                border: "1px solid #E2E8F0",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "500",
                color: "#2D3748",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}
            >
              👥 Usuarios
            </button>
            {onLogout && (
              <button
                onClick={() => {
                  onLogout();
                  setMenuOpen(false);
                }}
                style={{
                  width: "100%",
                  padding: "12px",
                  backgroundColor: "#FED7D7",
                  border: "1px solid #FC8181",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "500",
                  color: "#C53030",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px"
                }}
              >
                🚪 Cerrar Sesión
              </button>
            )}
          </div>
        )}

        {menuView === "history" && (
          <div>
            <div style={{ padding: "12px 16px", borderBottom: "1px solid #E2E8F0", display: "flex", alignItems: "center", gap: "10px" }}>
              <button
                onClick={() => setMenuView("main")}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: "18px",
                  cursor: "pointer",
                  padding: "4px"
                }}
              >
                ←
              </button>
              <span style={{ fontSize: "16px", fontWeight: "bold", color: "#2D3748" }}>Historial</span>
            </div>
            <RouteHistory 
              onRouteSelect={handleRouteSelect}
              onClose={() => {
                setMenuOpen(false);
                setMenuView("main");
              }}
            />
          </div>
        )}
      </div>

      <div className="search-box" style={{ padding: "16px" }}>
        {/* ORIGEN */}
        <div style={{ position: 'relative', marginBottom: "12px" }}>
          <div className="input-group">
            <span className="icon start">●</span>
            <input
              type="text"
              placeholder="Selecciona el Inicio"
              value={origin}
              onChange={(e) => {
                setOrigin(e.target.value);
                setOriginCoords(null);
                handleAutocomplete(e.target.value, "origin");
                setActiveField("origin");
              }}
            />
          </div>

          {activeField === "origin" && originSuggestions.length > 0 && (
            <ul className="suggestions-box">
              {originSuggestions.map((item, idx) => (
                <li key={idx} onClick={() => selectSuggestion(item, "origin")}>
                  {item.label}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* DESTINO */}
        <div style={{ position: 'relative', marginBottom: "12px" }}>
          <div className="input-group">
            <span className="icon end">📍</span>
            <input
              type="text"
              placeholder="Selecciona tu Destino (mín. 3 caracteres)"
              value={destination}
              onChange={(e) => {
                setDestination(e.target.value);
                setDestinationCoords(null);
                handleAutocomplete(e.target.value, "destination");
                setActiveField("destination");
              }}
              onKeyDown={onKeyDownDestination}
            />
          </div>

          {activeField === "destination" && destinationSuggestions.length > 0 && (
            <ul className="suggestions-box">
              {destinationSuggestions.map((item, idx) => (
                <li key={idx} onClick={() => selectSuggestion(item, "destination")}>
                  {item.label}
                </li>
              ))}
            </ul>
          )}

          {autocompleteError && <div style={{ color: 'red', marginTop: 6 }}>{autocompleteError}</div>}
        </div>

        <button 
          className="search-button" 
          onClick={handleSearchClick} 
          disabled={!originCoords || !destinationCoords}
          style={{
            width: "100%",
            padding: "12px",
            backgroundColor: originCoords && destinationCoords ? "#4FD1C5" : "#CBD5E0",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: originCoords && destinationCoords ? "pointer" : "not-allowed",
            fontSize: "16px",
            fontWeight: "bold"
          }}
        >
          Buscar ruta
        </button>
      </div>
    </div>
  );
}
