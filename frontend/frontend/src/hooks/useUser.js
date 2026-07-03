// useUser.js — har page yeh hook use karega logged-in user padhne ke liye
// Usage: const { userId, userName, isLoggedIn, logout } = useUser();

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export function useUser() {
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const id = localStorage.getItem("ms_user_id");
    const name = localStorage.getItem("ms_user_name");
    setUserId(id);
    setUserName(name);
  }, []);

  const logout = () => {
    localStorage.removeItem("ms_user_id");
    localStorage.removeItem("ms_user_name");
    setUserId(null);
    setUserName(null);
    navigate("/auth");
  };

  return {
    userId,
    userName,
    isLoggedIn: !!userId,
    logout,
  };
}