import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Register from "./components/Register";
import Users from "./components/Users";
import Home from "./pages/Home";

function App() {
  const isLogged = !!localStorage.getItem("user");

  return (
    <BrowserRouter>
      <Routes>
        {/* Login */}
        <Route path="/login" element={<Login />} />
        
        {/* Register */}
        <Route path="/register" element={<Register />} />
        
        {/* Home protegido (tu mapa de rutas) */}
        <Route 
          path="/home" 
          element={isLogged ? <Home /> : <Navigate to="/login" />} 
        />
        
        {/* Usuarios protegido */}
        <Route 
          path="/usuarios" 
          element={isLogged ? <Users /> : <Navigate to="/login" />} 
        />
        
        {/* Redireccion raiz */}
        <Route 
          path="/" 
          element={<Navigate to={isLogged ? "/home" : "/login"} />} 
        />
        
        {/* Rutas no existentes */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
