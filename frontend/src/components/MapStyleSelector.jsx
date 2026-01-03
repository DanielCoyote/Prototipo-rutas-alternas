import { useMap } from "react-leaflet";
import { useEffect, useState } from "react";
import L from "leaflet";

const mapStyles = {
  standard: {
    name: "Estándar",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; OpenStreetMap contributors',
    preview: "🗺️"
  },
  positron: {
    name: "Claro",
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; OpenStreetMap, &copy; CartoDB',
    preview: "☀️"
  },
  voyager: {
    name: "Voyager",
    url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    attribution: '&copy; OpenStreetMap, &copy; CartoDB',
    preview: "🌍"
  },
  dark: {
    name: "Oscuro",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; OpenStreetMap, &copy; CartoDB',
    preview: "🌙"
  },
  topo: {
    name: "Topográfico",
    url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attribution: '&copy; OpenStreetMap, &copy; OpenTopoMap',
    preview: "⛰️"
  },
  esri: {
    name: "Satélite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; Esri',
    preview: "🛰️"
  }
};

export default function MapStyleSelector({ onStyleChange }) {
  const map = useMap();
  const [isOpen, setIsOpen] = useState(false);
  const [currentStyle, setCurrentStyle] = useState('standard');

  useEffect(() => {
    const StyleControl = L.Control.extend({
      onAdd: function() {
        const container = L.DomUtil.create('div', 'map-style-selector');
        
        const btn = L.DomUtil.create('button', 'style-selector-btn', container);
        btn.innerHTML = '🗺️';
        btn.title = 'Cambiar estilo del mapa';
        
        const menu = L.DomUtil.create('div', 'style-selector-menu', container);
        menu.style.display = 'none';
        
        Object.entries(mapStyles).forEach(([key, style]) => {
          const option = L.DomUtil.create('div', 'style-option', menu);
          
          const preview = L.DomUtil.create('div', 'style-preview', option);
          preview.innerHTML = style.preview;
          
          const label = L.DomUtil.create('div', 'style-label', option);
          label.textContent = style.name;
          
          if (key === currentStyle) {
            option.classList.add('active');
          }
          
          L.DomEvent.on(option, 'click', function(e) {
            L.DomEvent.stopPropagation(e);
            L.DomEvent.preventDefault(e);
            setCurrentStyle(key);
            if (onStyleChange) {
              onStyleChange(key, style);
            }
            menu.style.display = 'none';
            setIsOpen(false);
            
            // Update active state
            menu.querySelectorAll('.style-option').forEach(opt => {
              opt.classList.remove('active');
            });
            option.classList.add('active');
          });
        });
        
        L.DomEvent.on(btn, 'click', function(e) {
          L.DomEvent.stopPropagation(e);
          L.DomEvent.preventDefault(e);
          const isCurrentlyOpen = menu.style.display === 'block';
          menu.style.display = isCurrentlyOpen ? 'none' : 'block';
          setIsOpen(!isCurrentlyOpen);
        });
        
        // Prevent map interactions on the control
        L.DomEvent.disableClickPropagation(container);
        L.DomEvent.disableScrollPropagation(container);
        
        return container;
      }
    });

    const styleControl = new StyleControl({ position: 'bottomright' });
    styleControl.addTo(map);

    return () => {
      map.removeControl(styleControl);
    };
  }, [map, currentStyle, onStyleChange]);

  return null;
}
