# Prototipo Rutas Alternas

Este proyecto es un prototipo de frontend (React + Vite) que usa OpenRouteService para autocompletar direcciones y obtener rutas.

## Backend (FastAPI)

He añadido un backend minimalista que actúa como proxy para OpenRouteService y oculta la clave.

### Cómo ejecutar el backend (local)

1. Copia `.env.example` a `backend/.env` y añade tu clave:

   ORS_API_KEY=tu_api_key_aqui

2. Desde PowerShell (en la raíz `backend`):

   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r app/requirements.txt

   ### Ejecuta uvicorn desde la raíz del paquete para evitar errores de import relativos:
   uvicorn app.main:app --reload --port 8000

   ### Alternativamente, si estás dentro de `backend/app`, puedes usar:
   uvicorn main:app --reload --port 8000

   (si usas este comando se aplica el fallback de import en `main.py`, pero preferimos la forma del paquete)

   ## DEBUG & fallback local
    - Para ayudar a depurar, puedes pedir metadata de diagnóstico añadiendo `?debug=true` al endpoint `/api/route`.
      En ese caso la respuesta incluirá `"source": "ors"` o `"source": "local"` indicando qué motor proporcionó la ruta.
    - Si ORS falla y quieres forzar probar el fallback local, asegúrate de tener instalado `osmnx` y `networkx` (recomendado con conda en Windows).

El backend expondrá:
- POST `/api/autocomplete`  { text }
- POST `/api/route`  { origin: [lon, lat], destination: [lon, lat] }
**Nota (opcional):** El backend puede usar un *fallback* de ruteo local (A* sobre OSM) si OpenRouteService falla, pero requiere `osmnx` y `networkx` instalados. En Windows se recomienda instalarlos vía `conda` por compatibilidad de dependencias.## Frontend

El frontend ya está modificado para usar el backend: `frontend/src/services/ors.js` hace las llamadas a `/api/*`.

Para ejecutar el frontend:

cd frontend
npm install
npm run dev

Abre http://localhost:5173
