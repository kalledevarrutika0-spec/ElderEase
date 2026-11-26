import { lazy, Suspense, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell.jsx";
import { LoadingState } from "./components/UI.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import { api } from "./services/api.js";

const AssistantPage = lazy(() => import("./pages/AssistantPage.jsx"));
const CalendarPage = lazy(() => import("./pages/CalendarPage.jsx"));
const DashboardPage = lazy(() => import("./pages/DashboardPage.jsx"));
const FamilyPage = lazy(() => import("./pages/FamilyPage.jsx"));
const MedicinesPage = lazy(() => import("./pages/MedicinesPage.jsx"));

function ProfileGuard({ children }) {
  const [checking, setChecking] = useState(true);
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    let active = true;
    api.familyProfile()
      .then(() => { if (active) setHasProfile(true); })
      .catch(() => { if (active) setHasProfile(false); })
      .finally(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, []);

  if (checking) return <LoadingState />;
  if (!hasProfile) return <Navigate to="/profile" replace />;
  return children;
}

export default function App() {
  const { session, loading } = useAuth();

  if (loading) return <LoadingState />;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={!session ? <LoginPage /> : <Navigate to="/profile" replace />} />
        <Route path="/profile" element={session ? <ProfilePage /> : <Navigate to="/login" replace />} />
        <Route element={session ? <ProfileGuard><AppShell /></ProfileGuard> : <Navigate to="/login" replace />}>
          <Route index element={<Suspense fallback={<LoadingState />}><DashboardPage /></Suspense>} />
          <Route path="medicines" element={<Suspense fallback={<LoadingState />}><MedicinesPage /></Suspense>} />
          <Route path="calendar" element={<Suspense fallback={<LoadingState />}><CalendarPage /></Suspense>} />
          <Route path="family" element={<Suspense fallback={<LoadingState />}><FamilyPage /></Suspense>} />
          <Route path="assistant" element={<Suspense fallback={<LoadingState />}><AssistantPage /></Suspense>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
