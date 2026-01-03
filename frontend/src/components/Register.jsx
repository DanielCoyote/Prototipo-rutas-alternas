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
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import { useNavigate } from "react-router-dom";
import { useUser } from '../context/UserContext';
import { registerUser } from '../services/api';

export default function Register() {
  const navigate = useNavigate();
  const { login } = useUser();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [name, setName] = useState("");

  const [emailError, setEmailError] = useState(false);
  const [pwdError, setPwdError] = useState(false);
  const [confirmError, setConfirmError] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    let valid = true;

    if (email.trim() === "") {
      setEmailError(true);
      valid = false;
    } else {
      setEmailError(false);
    }

    if (password.trim().length < 6) {
      setPwdError(true);
      valid = false;
    } else {
      setPwdError(false);
    }

    if (confirmPwd !== password || confirmPwd === "") {
      setConfirmError(true);
      valid = false;
    } else {
      setConfirmError(false);
    }

    if (!valid) return;

    setLoading(true);
    setError("");

    try {
      const response = await registerUser(email, password, name || null);
      
      // Iniciar sesión automáticamente después del registro
      login(response.token, {
        user_id: response.user_id,
        email: response.email,
        name: response.name
      });

      // Redirigir a home
      navigate("/home");
    } catch (err) {
      setError(err.message || "Error al registrarse");
    } finally {
      setLoading(false);
    }
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
          maxWidth: 450,
          borderRadius: 4,
          paddingY: 3,
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
            <PersonAddIcon fontSize="large" />
          </Avatar>

          <Typography variant="h5" sx={{ fontWeight: 700, color: "#1e88e5" }}>
            Crear cuenta
          </Typography>

          {error && (
            <Alert severity="error" sx={{ width: '100%' }}>
              {error}
            </Alert>
          )}

          <TextField
            label="Nombre (opcional)"
            type="text"
            fullWidth
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={loading}
          />

          <TextField
            label="Usuario o correo"
            type="text"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={emailError}
            helperText={emailError ? "Debe ingresar un usuario o correo" : ""}
            disabled={loading}
          />

          <TextField
            label="Contraseña"
            type="password"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={pwdError}
            helperText={
              pwdError ? "La contraseña debe tener al menos 6 caracteres" : ""
            }
            disabled={loading}
          />

          <TextField
            label="Confirmar contraseña"
            type="password"
            fullWidth
            value={confirmPwd}
            onChange={(e) => setConfirmPwd(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleRegister()}
            error={confirmError}
            helperText={
              confirmError ? "Las contraseñas no coinciden" : ""
            }
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
            onClick={handleRegister}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : "Registrarme"}
          </Button>

          <Typography variant="body2" sx={{ mt: 1 }}>
            ¿Ya tienes una cuenta?{" "}
            <Link
              component="button"
              onClick={() => navigate("/login")}
              sx={{ color: "#1e88e5", fontWeight: "bold" }}
            >
              Inicia sesión
            </Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
