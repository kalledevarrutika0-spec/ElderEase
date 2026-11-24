import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell.jsx";
import { LoadingState } from "./components/UI.jsx";

const AssistantPage = lazy(() => import("./pages/AssistantPage.jsx"));
const CalendarPage = lazy(() => import("./pages/CalendarPage.jsx"));
const DashboardPage = lazy(() => import("./pages/DashboardPage.jsx"));
const FamilyPage = lazy(() => import("./pages/FamilyPage.jsx"));
const MedicinesPage = lazy(() => import("./pages/MedicinesPage.jsx"));

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
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
