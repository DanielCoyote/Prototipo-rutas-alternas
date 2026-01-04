import { useState } from "react";
import { useNavigate } from "react-router-dom";
import RouteHistory from "./RouteHistory";
import FavoritesList from "./FavoritesList";
import "../styles/sidebar.css";

export default function Sidebar({ isOpen, onClose, onLogout, onRouteFromHistory, onFavoriteSelect }) {
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState("main"); // "main" | "history" | "favorites"

  const handleBackToMain = () => {
    setCurrentView("main");
  };

  const handleRouteSelect = (routeData) => {
    if (onRouteFromHistory) {
      onRouteFromHistory(routeData.origin, routeData.destination);
    }
    onClose();
  };

  const handleFavoriteSelect = (coords, label) => {
    if (onFavoriteSelect) {
      onFavoriteSelect(coords, label);
    }
    onClose();
  };

  return (
    <>
      {/* Overlay */}
      <div 
        className={`sidebar-overlay ${isOpen ? 'active' : ''}`}
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="sidebar-header">
          <button className="sidebar-close-btn" onClick={onClose}>
            ✕
          </button>
          <h2 className="sidebar-title">Menú</h2>
        </div>

        {/* Content */}
        <div className="sidebar-content">
          {currentView === "main" && (
            <div className="sidebar-menu">
              <button 
                className="sidebar-menu-item"
                onClick={() => setCurrentView("history")}
              >
                <span className="sidebar-menu-icon">📜</span>
                <span className="sidebar-menu-text">Historial de Rutas</span>
                <span className="sidebar-menu-arrow">›</span>
              </button>

              <button 
                className="sidebar-menu-item"
                onClick={() => setCurrentView("favorites")}
              >
                <span className="sidebar-menu-icon">⭐</span>
                <span className="sidebar-menu-text">Lugares Favoritos</span>
                <span className="sidebar-menu-arrow">›</span>
              </button>

              <button 
                className="sidebar-menu-item"
                onClick={() => {
                  navigate("/usuarios");
                  onClose();
                }}
              >
                <span className="sidebar-menu-icon">👥</span>
                <span className="sidebar-menu-text">Usuarios</span>
                <span className="sidebar-menu-arrow">›</span>
              </button>

              <div className="sidebar-divider" />

              <button 
                className="sidebar-menu-item danger"
                onClick={() => {
                  onLogout();
                  onClose();
                }}
              >
                <span className="sidebar-menu-icon">🚪</span>
                <span className="sidebar-menu-text">Cerrar Sesión</span>
              </button>
            </div>
          )}

          {currentView === "history" && (
            <div className="sidebar-view">
              <div className="sidebar-view-header">
                <button className="sidebar-back-btn" onClick={handleBackToMain}>
                  ‹ Atrás
                </button>
                <h3 className="sidebar-view-title">Historial de Rutas</h3>
              </div>
              <div className="sidebar-view-content">
                <RouteHistory 
                  onRouteSelect={handleRouteSelect}
                  onClose={onClose}
                />
              </div>
            </div>
          )}

          {currentView === "favorites" && (
            <div className="sidebar-view">
              <div className="sidebar-view-header">
                <button className="sidebar-back-btn" onClick={handleBackToMain}>
                  ‹ Atrás
                </button>
                <h3 className="sidebar-view-title">Lugares Favoritos</h3>
              </div>
              <div className="sidebar-view-content">
                <FavoritesList 
                  onClose={onClose}
                  onFavoriteSelect={handleFavoriteSelect}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
