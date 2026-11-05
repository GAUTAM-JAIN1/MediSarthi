// Single source of truth for backend URL and external links.
// Dev: falls back to localhost. Prod: set VITE_API_BASE in the hosting dashboard.
export const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8080";

// Jan Aushadhi store locator. Verify the exact path before deploy.
export const JANAUSHADHI_LOCATOR_URL = "https://janaushadhi.gov.in/";