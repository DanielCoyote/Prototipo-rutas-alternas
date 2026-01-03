/**
 * API service for making authenticated HTTP requests to the backend
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * Get authentication headers with JWT token
 */
export function getAuthHeaders() {
  const token = localStorage.getItem('token');
  
  if (token) {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }
  
  return {
    'Content-Type': 'application/json'
  };
}

/**
 * Register a new user
 */
export async function registerUser(email, password, name = null) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error en el registro');
  }
  
  return response.json();
}

/**
 * Login user
 */
export async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error en el inicio de sesión');
  }
  
  return response.json();
}

/**
 * Get current user information
 */
export async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: 'GET',
    headers: getAuthHeaders()
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error al obtener usuario');
  }
  
  return response.json();
}
