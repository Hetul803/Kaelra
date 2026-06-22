import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { getDeviceId, getDeviceKind, getDeviceName } from "../lib/device";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const heartbeat = useCallback(async () => {
    try {
      await api.post("/devices/heartbeat", {
        device_id: getDeviceId(),
        name: getDeviceName(),
        kind: getDeviceKind(),
        voice_enabled: false,
      });
    } catch (e) {
      /* ignore */
    }
  }, []);

  const loadMe = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data.user);
      setProfile(data.profile);
      heartbeat();
      return data.user;
    } catch (e) {
      setUser(null);
      setProfile(null);
      return null;
    }
  }, [heartbeat]);

  useEffect(() => {
    const token = localStorage.getItem("kaelra_token");
    if (!token) {
      setLoading(false);
      return;
    }
    loadMe().finally(() => setLoading(false));
  }, [loadMe]);

  // Keep device "active" while the tab is open
  useEffect(() => {
    if (!user) return;
    const t = setInterval(heartbeat, 60000);
    return () => clearInterval(t);
  }, [user, heartbeat]);

  const persist = (data) => {
    localStorage.setItem("kaelra_token", data.token);
    setUser(data.user);
  };

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    persist(data);
    await loadMe();
    return data.user;
  };

  const signup = async (email, password, name) => {
    const { data } = await api.post("/auth/signup", { email, password, name });
    persist(data);
    await loadMe();
    return data.user;
  };

  const demoLogin = async () => {
    const { data } = await api.post("/auth/demo");
    persist(data);
    await loadMe();
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem("kaelra_token");
    setUser(null);
    setProfile(null);
    window.location.href = "/auth";
  };

  const refreshProfile = loadMe;

  return (
    <AuthContext.Provider
      value={{ user, profile, loading, login, signup, demoLogin, logout, refreshProfile, setUser, setProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}
