import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Register from "./components/Register";
import Users from "./components/Users";
import Home from "./pages/Home";
import { UserProvider, useUser } from "./context/UserContext";
import { CircularProgress, Box } from "@mui/material";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useUser();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return isAuthenticated() ? children : <Navigate to="/login" />;
}

function AppRoutes() {
  const { isAuthenticated, loading } = useUser();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Routes>
      {/* Login */}
      <Route path="/login" element={<Login />} />
      
      {/* Register */}
      <Route path="/register" element={<Register />} />
      
      {/* Home protegido (tu mapa de rutas) */}
      <Route 
        path="/home" 
        element={
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        } 
      />
      
      {/* Usuarios protegido */}
      <Route 
        path="/usuarios" 
        element={
          <ProtectedRoute>
            <Users />
          </ProtectedRoute>
        } 
      />
      
      {/* Redirección raíz */}
      <Route 
        path="/" 
        element={<Navigate to={isAuthenticated() ? "/home" : "/login"} />} 
      />
      
      {/* Rutas no existentes */}
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

function App() {
  return (
    <UserProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </UserProvider>
  );
}

export default App;
