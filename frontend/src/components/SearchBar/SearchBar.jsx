import "./SearchBar.css";
import { useState, useEffect, useRef } from "react";
import { autocomplete } from "../../services/ors";

export default function SearchBar({ onSearch }) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);

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
        console.log(`${field} results:`, results);
        
        if (field === "origin") {
          setOriginSuggestions(results);
        } else {
          setDestinationSuggestions(results);
        }
      } catch (error) {
        console.error(`Error fetching ${field} suggestions:`, error);
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
      setOriginSuggestions([]);
      setActiveField(null);
    } else {
      setDestination(item.label);
      setDestinationSuggestions([]);
      setActiveField(null);
    }
  };

  return (
    <div className="search-container">
      <div className="search-header">
        <button className="menu-btn">☰</button>
        <h2>Direcciones de Viaje</h2>
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
                handleAutocomplete(e.target.value, "destination");
                setActiveField("destination");
              }}
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
        </div>
      </div>
    </div>
  );
}
