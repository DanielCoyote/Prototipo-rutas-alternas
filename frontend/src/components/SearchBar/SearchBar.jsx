import "./SearchBar.css";
import { useState, useEffect, useRef } from "react";
import { autocomplete } from "../../services/ors";

export default function SearchBar({ onSearch, externalDestination, onMenuToggle, avoidZones, setAvoidZones }) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const [originCoords, setOriginCoords] = useState(null);
  const [destinationCoords, setDestinationCoords] = useState(null);

  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [autocompleteError, setAutocompleteError] = useState(null);

  const [activeField, setActiveField] = useState(null);

  const debounceTimerRef = useRef(null);

  const handleUseCurrentLocation = (field) => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          // Store in [lon, lat] format for consistency with ORS API
          const coords = [longitude, latitude];
          const label = `Mi ubicación (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`;
          
          if (field === "origin") {
            setOrigin(label);
            setOriginCoords(coords);
          } else {
            setDestination(label);
            setDestinationCoords(coords);
          }
        },
        (error) => {
          console.error("Error obteniendo ubicación:", error);
          alert("No se pudo obtener tu ubicación. Verifica los permisos del navegador.");
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

  return (
    <div className="search-container" style={{ width: "400px" }}>
      <div className="search-header" style={{ display: 'flex', gap: 10, alignItems: 'center', padding: "12px 16px" }}>
        <button 
          className="menu-btn"
          onClick={onMenuToggle}
          style={{
            background: "transparent",
            color: "#2D3748",
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

      {/* Toggle para evitar zonas de riesgo */}
      <div style={{ padding: "12px 16px", backgroundColor: "#F7FAFC", borderBottom: "1px solid #E2E8F0" }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: "14px", fontWeight: "500", color: "#2D3748" }}>
            🚫 Evitar zonas de riesgo inundables
          </span>
          <div 
            className={`toggle-switch ${avoidZones ? 'active' : ''}`}
            onClick={() => setAvoidZones(!avoidZones)}
          >
            <div className="toggle-slider">
              <span className="toggle-icon">
                {avoidZones ? '✓' : '✕'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="search-box" style={{ padding: "16px" }}>
        {/* ORIGEN */}
        <div style={{ position: 'relative', marginBottom: "12px" }}>
          <div className="input-group" style={{ display: 'flex', gap: '8px' }}>
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
              style={{ flex: 1 }}
            />
            <button
              onClick={() => handleUseCurrentLocation("origin")}
              style={{
                background: "#4FD1C5",
                border: "none",
                borderRadius: "6px",
                padding: "8px 12px",
                cursor: "pointer",
                fontSize: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}
              title="Usar mi ubicación actual"
            >
              📍
            </button>
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
          <div className="input-group" style={{ display: 'flex', gap: '8px' }}>
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
              style={{ flex: 1 }}
            />
            <button
              onClick={() => handleUseCurrentLocation("destination")}
              style={{
                background: "#4FD1C5",
                border: "none",
                borderRadius: "6px",
                padding: "8px 12px",
                cursor: "pointer",
                fontSize: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}
              title="Usar mi ubicación actual"
            >
              📍
            </button>
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
