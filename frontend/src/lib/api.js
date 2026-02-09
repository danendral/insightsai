/**
 * API Client - Handles all communication with the FastAPI backend.
 *
 * KEY CONCEPT - Frontend-Backend Communication:
 * The React frontend and FastAPI backend are separate applications.
 * They communicate over HTTP using JSON:
 *
 *   React (port 5173) --HTTP request--> FastAPI (port 8000)
 *   React (port 5173) <--JSON response-- FastAPI (port 8000)
 *
 * This file centralizes all API calls so components don't need to
 * know about URLs or fetch() details.
 */

const API_BASE = "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Request failed");
  }
  return res.json();
}

/** Load the built-in sample dataset */
export function loadSampleData() {
  return request("/api/sample");
}

/** Upload a CSV file */
export function uploadCSV(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/api/upload", { method: "POST", body: formData });
}

/** Get dataset summary stats */
export function getDataSummary() {
  return request("/api/data");
}

/** Get paginated raw data */
export function getRawData(page = 1, pageSize = 50) {
  return request(`/api/data/raw?page=${page}&page_size=${pageSize}`);
}

/** Get chart data by type */
export function getChartData(chartType) {
  return request(`/api/charts/${chartType}`);
}

/** Ask a natural language question about the data */
export function queryData(question) {
  return request("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}
