import { supabase } from "./supabase.js";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://elderease-i71f.onrender.com";

async function request(path, options = {}) {
  let authorization;
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) authorization = `Bearer ${data.session.access_token}`;
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(authorization ? { Authorization: authorization } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      message = body.error?.message || message;
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}

const list = (path) => request(`${path}?offset=0&limit=500`);
const json = (method, body) => ({ method, body: JSON.stringify(body) });

export const api = {
  familyProfile: () => request("/api/family/profile"),
  createFamilyProfile: (payload) =>
    request("/api/family/profile", json("POST", payload)),
  updateFamilyProfile: (payload) =>
    request("/api/family/profile", json("PUT", payload)),
  linkFamilyMember: (payload) =>
    request("/api/family/members/link", json("POST", payload)),
  health: (signal) => request("/api/health", { signal }),
  dashboard: () => request("/api/dashboard/overview"),
  medicines: () => list("/api/medicines"),
  dosesToday: () => list("/api/doses/today"),
  refillForecasts: () => list("/api/medicines/refill-forecast"),
  appointments: () => list("/api/appointments"),
  caregivers: () => list("/api/caregivers"),
  notifications: () => list("/api/notifications"),
  assistantChat: (message) =>
    request("/api/assistant/chat", json("POST", { message })),
  stock: (medicineId) => request(`/api/medicines/${medicineId}/stock`),
  createMedicine: (payload) =>
    request("/api/medicines", json("POST", payload)),
  updateMedicine: (medicineId, payload) =>
    request(`/api/medicines/${medicineId}`, json("PUT", payload)),
  adjustStock: (medicineId, payload) =>
    request(`/api/medicines/${medicineId}/stock`, json("POST", payload)),
  logDose: (doseId, status) =>
    request(`/api/doses/${doseId}/log`, json("POST", { status })),
  createAppointment: (payload) =>
    request("/api/appointments", json("POST", payload)),
  updateAppointment: (appointmentId, payload) =>
    request(`/api/appointments/${appointmentId}`, json("PUT", payload)),
  deleteAppointment: (appointmentId) =>
    request(`/api/appointments/${appointmentId}`, { method: "DELETE" }),
  acknowledgeNotification: (notificationId) =>
    request(`/api/notifications/${notificationId}/acknowledge`, {
      method: "PATCH",
    }),
};

export async function fetchHealth(signal) {
  return api.health(signal);
}
