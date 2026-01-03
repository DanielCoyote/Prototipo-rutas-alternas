// Now requests go through the local backend proxy at /api/*

export async function autocomplete(query) {
  if (!query) return [];

  try {
    const response = await fetch(`/api/autocomplete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: query })
    });

    if (!response.ok) {
      const body = await response.text();
      console.error('Autocomplete proxy error', response.status, body);
      // throw so UI can show a message
      throw new Error(`Autocomplete failed: ${response.status}`);
    }

    const data = await response.json();
    return data.map(item => ({ label: item.label, coords: item.coords }));
  } catch (err) {
    console.error('Network error during autocomplete', err);
    throw new Error('Network error during autocomplete');
  }
}

export async function getRoute(originCoords, destCoords, avoidPolygons = null) {
  if (!originCoords || !destCoords) return null;

  try {
    const body = { origin: originCoords, destination: destCoords };
    if (avoidPolygons) body.avoid_polygons = avoidPolygons;

    const response = await fetch(`/api/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const body = await response.text();
      console.error('Route proxy error', response.status, body);
      throw new Error(body || `Route proxy error: ${response.status}`);
    }

    const data = await response.json();
    // data.routes is now an array of route objects
    // Each route has: { coords: [[lat, lon], ...], duration: minutes, distance: km }
    return { 
      routes: data.routes || []
    };
  } catch (err) {
    console.error('Network error during getRoute', err);
    throw err;
  }
}
