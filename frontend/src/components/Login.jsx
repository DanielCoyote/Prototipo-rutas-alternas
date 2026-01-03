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
} from "@mui/material";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [emailError, setEmailError] = useState(false);
  const [passwordError, setPasswordError] = useState(false);

  const handleLogin = () => {
    let valid = true;

    if (!email.includes("@")) {
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

    // Guardar sesión
    localStorage.setItem("user", email);

    // Redirigir a home (mapa)
    navigate("/home");
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

          <TextField
            label="Correo electrónico"
            type="email"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={emailError}
            helperText={emailError ? "Ingresa un correo válido" : ""}
          />

          <TextField
            label="Contraseña"
            type="password"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={passwordError}
            helperText={passwordError ? "La contraseña no puede estar vacía" : ""}
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
          >
            Ingresar
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
