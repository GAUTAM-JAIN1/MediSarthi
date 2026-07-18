// useUser.js — har page yeh hook use karega logged-in user + auth token padhne ke liye
// Usage: const { userId, userName, token, isLoggedIn, logout, authFetch } = useUser();

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

export function useUser() {
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState(null);
  const [token, setToken] = useState(null); // NEW (D34)
  const navigate = useNavigate();

  useEffect(() => {
    const id = localStorage.getItem("ms_user_id");
    const name = localStorage.getItem("ms_user_name");
    const tok = localStorage.getItem("ms_token"); // NEW (D34)
    setUserId(id);
    setUserName(name);
    setToken(tok);
  }, []);

  const logout = () => {
    localStorage.removeItem("ms_user_id");
    localStorage.removeItem("ms_user_name");
    localStorage.removeItem("ms_token"); // NEW (D34)
    setUserId(null);
    setUserName(null);
    setToken(null);
    navigate("/auth");
  };

  /**
   * NEW (D34) — thin wrapper around fetch() that automatically attaches
   * the Authorization header. Backend now requires this header on every
   * endpoint except /auth/signup, /auth/login, the public
   * /health/qr/{token} and /health/doctor-qr/{token} views, and the root
   * health-check.
   *
   * Usage is identical to plain fetch() otherwise — same signature, same
   * Response object back — so swapping `fetch(url, opts)` ->
   * `authFetch(url, opts)` on protected calls is a mechanical
   * find-and-replace per page, not a rewrite of each call's logic.
   *
   * Works for both JSON requests (fetch(url, { method, headers, body }))
   * and FormData/multipart uploads (fetch(url, { method: "POST", body:
   * formData })) — it only ever adds the Authorization header, it never
   * touches or assumes anything about Content-Type, so file-upload calls
   * (voice/document consultation, lab report upload) keep working exactly
   * as before.
   */
  const authFetch = useCallback(
    (url, options = {}) => {
      const existingHeaders = options.headers || {};
      return fetch(url, {
        ...options,
        headers: {
          ...existingHeaders,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
    },
    [token]
  );

  return {
    userId,
    userName,
    token,
    isLoggedIn: !!userId && !!token,
    logout,
    authFetch,
  };
}