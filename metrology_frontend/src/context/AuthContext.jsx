import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { auth as authApi, getToken, setToken } from "../lib/api";

const REFRESH_INTERVAL_MS = 12 * 60 * 60 * 1000; // refresh the token every 12h
const USER_KEY = "metrology_user";

const AuthContext = createContext(null);

function readStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function storeUser(user) {
  try {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  } catch {
    // storage unavailable - session still works, just without offline restore
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [offline, setOffline] = useState(false);
  const refreshTimerRef = useRef(null);

  const applyUser = (u) => {
    setUser(u);
    storeUser(u);
  };

  const scheduleTokenRefresh = () => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    // Only refresh while a user is actually logged in.
    refreshTimerRef.current = setTimeout(async () => {
      if (!getToken()) return;
      try {
        const result = await authApi.refresh();
        setToken(result.access_token);
        applyUser(result.user);
      } catch (err) {
        // Network hiccup (backend restarting): keep the token and retry later
        // instead of logging the user out. A 401 means the token is truly
        // invalid/expired, which is the only case that should end the session.
        if (err?.status === 401) {
          setToken(null);
          applyUser(null);
        }
      }
    }, REFRESH_INTERVAL_MS);
  };

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((u) => {
        applyUser(u);
        setOffline(false);
        scheduleTokenRefresh();
      })
      .catch((err) => {
        if (!err?.status) {
          // Backend unreachable (restarting / offline): restore the cached
          // profile so the user is NOT logged out while the server is down.
          const cached = readStoredUser();
          if (cached) {
            applyUser(cached);
            setOffline(true);
            scheduleTokenRefresh();
          } else {
            setToken(null);
            applyUser(null);
          }
        } else {
          // 401 etc: token is genuinely invalid.
          setToken(null);
          applyUser(null);
        }
      })
      .finally(() => setLoading(false));

    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When connectivity comes back, re-sync with the server and clear the
  // offline banner automatically.
  useEffect(() => {
    const onOnline = () => {
      if (getToken()) {
        authApi
          .me()
          .then((u) => {
            applyUser(u);
            setOffline(false);
          })
          .catch(() => {});
      }
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email, password) => {
    setError("");
    try {
      const result = await authApi.login(email, password);
      setToken(result.access_token);
      applyUser(result.user);
      setOffline(false);
      scheduleTokenRefresh();
      return true;
    } catch (err) {
      setError(err.message || "Login failed");
      return false;
    }
  };

  const logout = () => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    setToken(null);
    applyUser(null);
    setOffline(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, offline, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
