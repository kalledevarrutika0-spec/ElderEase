import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell.jsx";
import { LoadingState } from "./components/UI.jsx";
import { ToastProvider } from "./components/Toast.jsx";
import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import LoginPage from "./pages/LoginPage.jsx";

const AssistantPage = lazy(() => import("./pages/AssistantPage.jsx"));
const CalendarPage = lazy(() => import("./pages/CalendarPage.jsx"));
const DashboardPage = lazy(() => import("./pages/DashboardPage.jsx"));
const FamilyPage = lazy(() => import("./pages/FamilyPage.jsx"));
const MedicinesPage = lazy(() => import("./pages/MedicinesPage.jsx"));

function RequireAuth() {
  const { user } = useAuth();
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="login" element={<LoginPage />} />
            <Route element={<RequireAuth />}>
              <Route element={<AppShell />}>
                <Route index element={<Suspense fallback={<LoadingState />}><DashboardPage /></Suspense>} />
                <Route path="medicines" element={<Suspense fallback={<LoadingState />}><MedicinesPage /></Suspense>} />
                <Route path="calendar" element={<Suspense fallback={<LoadingState />}><CalendarPage /></Suspense>} />
                <Route path="family" element={<Suspense fallback={<LoadingState />}><FamilyPage /></Suspense>} />
                <Route path="assistant" element={<Suspense fallback={<LoadingState />}><AssistantPage /></Suspense>} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}