import React, { useState } from "react";
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Avatar,
  Link,
  Alert,
  CircularProgress,
} from "@mui/material";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import { useNavigate } from "react-router-dom";
import { useUser } from '../context/UserContext';
import { loginUser } from '../services/api';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useUser();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [emailError, setEmailError] = useState(false);
  const [passwordError, setPasswordError] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    let valid = true;

    if (email.trim() === "") {
      setEmailError(true);
      valid = false;
    } else {
      setEmailError(false);
    }

    if (password.trim() === "") {
      setPasswordError(true);
      valid = false;
    } else {
      setPasswordError(false);
    }

    if (!valid) return;

    setLoading(true);
    setError("");

    try {
      const response = await loginUser(email, password);
      
      // Guardar token y datos del usuario en el contexto
      login(response.token, {
        user_id: response.user_id,
        email: response.email,
        name: response.name
      });

      // Redirigir a home (mapa)
      navigate("/home");
    } catch (err) {
      setError(err.message || "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  const goToRegister = () => {
    navigate("/register");
  };

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding: 2,
      }}
    >
      <Card
        elevation={10}
        sx={{
          width: "100%",
          maxWidth: 420,
          borderRadius: 4,
          paddingY: 2,
        }}
      >
        <CardContent
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 3,
            textAlign: "center",
          }}
        >
          <Avatar
            sx={{
              margin: "0 auto",
              bgcolor: "#1e88e5",
              width: 64,
              height: 64,
            }}
          >
            <LockOutlinedIcon fontSize="large" />
          </Avatar>

          <Typography
            variant="h5"
            sx={{ fontWeight: 700, color: "#1e88e5" }}
          >
            Rutas Alternas - CDMX
          </Typography>

          {error && (
            <Alert severity="error" sx={{ width: '100%' }}>
              {error}
            </Alert>
          )}

          <TextField
            label="Usuario o correo"
            type="text"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={emailError}
            helperText={emailError ? "Ingresa tu usuario o correo" : ""}
            disabled={loading}
          />

          <TextField
            label="Contraseña"
            type="password"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
            error={passwordError}
            helperText={passwordError ? "La contraseña no puede estar vacía" : ""}
            disabled={loading}
          />

          <Button
            variant="contained"
            size="large"
            fullWidth
            sx={{
              borderRadius: 3,
              paddingY: 1.3,
              textTransform: "none",
            }}
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : "Ingresar"}
          </Button>

          <Typography variant="body2" sx={{ mt: 1 }}>
            ¿No tienes cuenta?{" "}
            <Link
              component="button"
              onClick={goToRegister}
              sx={{ color: "#1e88e5", fontWeight: "bold" }}
            >
              Regístrate
            </Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
