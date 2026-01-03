import "./SearchBar.css";
import { useState, useEffect, useRef } from "react";
import { autocomplete } from "../../services/ors";

export default function SearchBar({ onSearch, avoidZones = false, setAvoidZones = () => {} }) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  // We store coords as returned by ORS: [lon, lat]
  const [originCoords, setOriginCoords] = useState(null);
  const [destinationCoords, setDestinationCoords] = useState(null);

  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [autocompleteError, setAutocompleteError] = useState(null);

  const [activeField, setActiveField] = useState(null);

  // Referencias para los timers de debounce
  const debounceTimerRef = useRef(null);

  const handleAutocomplete = async (value, field) => {
    // Cancelar el timer anterior si existe
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Si el input está vacío, limpiar sugerencias inmediatamente
    if (!value || value.trim().length < 3) {
      if (field === "origin") {
        setOriginSuggestions([]);
      } else {
        setDestinationSuggestions([]);
      }
      return;
    }

    // Crear nuevo timer - esperar 500ms después de que el usuario deje de escribir
    debounceTimerRef.current = setTimeout(async () => {
      try {
        const results = await autocomplete(value);
        // console.log(`${field} results:`, results);
        setAutocompleteError(null);
        if (field === "origin") {
          setOriginSuggestions(results);
        } else {
          setDestinationSuggestions(results);
        }
      } catch (error) {
        console.error(`Error fetching ${field} suggestions:`, error);
        // clear after 3s
        setTimeout(() => setAutocompleteError(null), 3000);
        if (field === "origin") {
          setOriginSuggestions([]);
        } else {
          setDestinationSuggestions([]);
        }
      }
    }, 500); // 500ms de delay - ajusta según prefieras
  };

  // Limpiar el timer cuando el componente se desmonte
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const selectSuggestion = (item, field) => {
    if (field === "origin") {
      setOrigin(item.label);
      setOriginCoords(item.coords); // [lon, lat]
      setOriginSuggestions([]);
      setActiveField(null);
    } else {
      setDestination(item.label);
      setDestinationCoords(item.coords); // [lon, lat]
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
    <div className="search-container">
      <div className="search-header" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <button className="menu-btn">☰</button>
        <h2 style={{ margin: 0 }}>Direcciones de Viaje</h2>

        <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', background: 'white', padding: '4px 8px', borderRadius: 6 }}>
          <input
            type="checkbox"
            checked={avoidZones}
            onChange={(e) => setAvoidZones(e.target.checked)}
          />
          <span style={{ marginLeft: 8, fontSize: 12 }}>Evitar zonas inundables</span>
        </label>
      </div>

      <div className="search-box">
        {/* ORIGEN */}
        <div style={{ position: 'relative' }}>
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
        <div style={{ position: 'relative' }}>
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

        <div style={{ marginTop: 10 }}>
          <button className="search-button" onClick={handleSearchClick} disabled={!originCoords || !destinationCoords}>
            Buscar ruta
          </button>
        </div>
      </div>
    </div>
  );
}
