import { createContext, useContext, useState } from "react";

const STORAGE_KEY = "elderease_user";

// Demo account for the hackathon. Real accounts need backend auth (later).
const DEMO_ACCOUNTS = [
  { email: "family@elderease.com", password: "care1234", name: "Asha" },
];

const AuthContext = createContext(null);

function loadUser() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(loadUser);

  function login(email, password) {
    const account = DEMO_ACCOUNTS.find(
      (item) => item.email === email.trim().toLowerCase() && item.password === password
    );
    if (!account) throw new Error("Incorrect email or password.");
    const nextUser = { email: account.email, name: account.name };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
    } catch {
      /* storage unavailable: login still works for this session */
    }
    setUser(nextUser);
  }

  function logout() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}