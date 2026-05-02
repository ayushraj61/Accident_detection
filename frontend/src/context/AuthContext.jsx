import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [role, setRole] = useState(localStorage.getItem('role'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Cleanup stale/invalid storage
    if (token === 'null' || !token) {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      setToken(null);
      setRole(null);
      setLoading(false);
      return;
    }

    if (token && role) {
      console.log(`[Auth] Attempting auto-login with role: ${role}`);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserProfile(role);
    } else {
      setLoading(false);
    }
  }, [token, role]);

  const fetchUserProfile = async (currentRole) => {
    const activeRole = currentRole || role;
    if (!activeRole) {
      setLoading(false);
      return;
    }
    
    try {
      let endpoint = '';
      if (activeRole === 'hospital') endpoint = 'http://localhost:8000/api/v1/hospital/me';
      else if (activeRole === 'ambulance') endpoint = 'http://localhost:8000/api/v1/ambulance/me';
      else if (activeRole === 'admin') endpoint = 'http://localhost:8000/api/v1/admin/me';
      
      const response = await axios.get(endpoint);
      console.log("[Auth] Profile fetched successfully");
      setUser(response.data);
    } catch (error) {
      console.error("[Auth] Profile fetch failed:", error.response?.status || error.message);
      if (error.response?.status === 401) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, loginRole) => {
    console.log(`[Auth] Attempting login for ${email} as ${loginRole}`);
    try {
      const response = await axios.post('http://localhost:8000/api/v1/auth/login', {
        email,
        password,
        role: loginRole
      });
      const { access_token, role: userRole } = response.data;
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      localStorage.setItem('token', access_token);
      localStorage.setItem('role', userRole);
      
      setToken(access_token);
      setRole(userRole);
      
      await fetchUserProfile(userRole);
      return response.data;
    } catch (error) {
      console.error("[Auth] Login request failed:", error.response?.data || error.message);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setRole(null);
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    role,
    loading,
    login,
    logout,
    isAuthenticated: !!token
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
