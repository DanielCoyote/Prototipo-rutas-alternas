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
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");

  const [emailError, setEmailError] = useState(false);
  const [pwdError, setPwdError] = useState(false);
  const [confirmError, setConfirmError] = useState(false);

  const handleRegister = () => {
    let valid = true;

    if (!email.includes("@")) {
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

    localStorage.setItem("user", email);
    navigate("/login");
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

          <TextField
            label="Correo electrónico"
            type="email"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={emailError}
            helperText={emailError ? "Debe ingresar un correo válido" : ""}
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
          />

          <TextField
            label="Confirmar contraseña"
            type="password"
            fullWidth
            value={confirmPwd}
            onChange={(e) => setConfirmPwd(e.target.value)}
            error={confirmError}
            helperText={
              confirmError ? "Las contraseñas no coinciden" : ""
            }
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
          >
            Registrarme
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
