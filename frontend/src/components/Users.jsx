import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody
} from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function Users() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    nombre: "",
    rfc: "",
    tipoSangre: "",
    nacionalidad: "",
  });

  const [usuarios, setUsuarios] = useState([]);

  // Cargar usuarios guardados
  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("usuarios")) || [];
    setUsuarios(stored);
  }, []);

  // Manejar cambios de inputs
  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  // Guardar usuario
  const handleSave = () => {
    const updated = [...usuarios, form];
    setUsuarios(updated);
    localStorage.setItem("usuarios", JSON.stringify(updated));

    alert("Usuario registrado");

    setForm({
      nombre: "",
      rfc: "",
      tipoSangre: "",
      nacionalidad: "",
    });
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <Box sx={{ p: 4 }}>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: "bold" }}>
          Registro de Usuarios
        </Typography>
        <Button 
          variant="outlined" 
          onClick={() => navigate("/home")}
          sx={{ mr: 2 }}
        >
          Volver al Mapa
        </Button>
        <Button 
          variant="contained" 
          color="error"
          onClick={handleLogout}
        >
          Cerrar sesión
        </Button>
      </Box>

      <Grid container spacing={3}>

        {/* FORMULARIO */}
        <Grid item xs={12} md={5}>
          <Card sx={{ p: 3, background: "white", boxShadow: 4 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: "bold" }}>
                Registrar Usuario
              </Typography>

              <TextField
                label="Nombre completo"
                name="nombre"
                value={form.nombre}
                onChange={handleChange}
                fullWidth
                sx={{ mb: 2 }}
              />

              <TextField
                label="RFC"
                name="rfc"
                value={form.rfc}
                onChange={handleChange}
                fullWidth
                sx={{ mb: 2 }}
              />

              <TextField
                label="Tipo de sangre"
                name="tipoSangre"
                value={form.tipoSangre}
                onChange={handleChange}
                fullWidth
                sx={{ mb: 2 }}
              />

              <TextField
                label="Nacionalidad"
                name="nacionalidad"
                value={form.nacionalidad}
                onChange={handleChange}
                fullWidth
                sx={{ mb: 2 }}
              />

              <Button
                variant="contained"
                onClick={handleSave}
                sx={{
                  backgroundColor: "#0D47A1",
                  "&:hover": { backgroundColor: "#1565C0" },
                }}
                fullWidth
              >
                Guardar Usuario
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* TABLA DE USUARIOS */}
        <Grid item xs={12} md={7}>
          <Card sx={{ p: 3, background: "white", boxShadow: 4 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: "bold" }}>
                Usuarios Registrados ({usuarios.length})
              </Typography>

              {usuarios.length === 0 ? (
                <Typography color="textSecondary">
                  No hay usuarios registrados aún
                </Typography>
              ) : (
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Nombre</strong></TableCell>
                      <TableCell><strong>RFC</strong></TableCell>
                      <TableCell><strong>Tipo Sangre</strong></TableCell>
                      <TableCell><strong>Nacionalidad</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {usuarios.map((usuario, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{usuario.nombre}</TableCell>
                        <TableCell>{usuario.rfc}</TableCell>
                        <TableCell>{usuario.tipoSangre}</TableCell>
                        <TableCell>{usuario.nacionalidad}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Grid>

      </Grid>
    </Box>
  );
}
