const ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImFhYzc5Mzc1YzY3NTQyNjQ5NDIxOWNiYTM0YmIwNzFkIiwiaCI6Im11cm11cjY0In0=";

export async function autocomplete(query) {
  if (!query) return [];

  const url = `https://api.openrouteservice.org/geocode/autocomplete?api_key=${ORS_API_KEY}&text=${encodeURIComponent(query)}&boundary.country=MEX`;

  const response = await fetch(url);
  const data = await response.json();

  if (!data.features) return [];

  return data.features.map(item => ({
    label: item.properties.label,
    coords: item.geometry.coordinates
  }));
}
