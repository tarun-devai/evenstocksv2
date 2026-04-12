import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const username = Cookies.get('username');
    const userToken = Cookies.get('user_token');
    if (username && userToken) {
      setUser({ username, token: userToken });
      setIsLoggedIn(true);
    }
  }, []);

  const login = useCallback((username, token) => {
    Cookies.set('username', username, { path: '/', expires: 7 });
    Cookies.set('user_token', token, { path: '/', expires: 7 });
    setUser({ username, token });
    setIsLoggedIn(true);
  }, []);

  const logout = useCallback(() => {
    Cookies.remove('username', { path: '/' });
    Cookies.remove('user_token', { path: '/' });
    setUser(null);
    setIsLoggedIn(false);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
