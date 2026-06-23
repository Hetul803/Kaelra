import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import "./App.css";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";
import { AppShell } from "./components/AppShell";
import { KaelraOrb } from "./components/KaelraOrb";

import Auth from "./pages/Auth";
import GoogleCallback from "./pages/GoogleCallback";
import Onboarding from "./pages/Onboarding";
import Kaelra from "./pages/Kaelra";
import Today from "./pages/Today";
import Talk from "./pages/Talk";
import ActionQueue from "./pages/ActionQueue";
import Memory from "./pages/Memory";
import Files from "./pages/Files";
import Routines from "./pages/Routines";
import ConnectedAccounts from "./pages/ConnectedAccounts";
import Devices from "./pages/Devices";
import Settings from "./pages/Settings";
import Jobs from "./pages/Jobs";
import ClassSkill from "./pages/ClassSkill";
import Founder from "./pages/Founder";
import SmartHome from "./pages/SmartHome";

function FullLoader() {
  return (
    <div className="kaelra-app-bg flex min-h-screen flex-col items-center justify-center gap-4">
      <KaelraOrb size={96} state="thinking" />
      <p className="text-sm text-muted-foreground font-mono-k">Waking Kaelra…</p>
    </div>
  );
}

function Protected({ children, title }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullLoader />;
  if (!user) return <Navigate to="/auth" replace state={{ from: location }} />;
  if (!user.onboarded) return <Navigate to="/onboarding" replace />;
  return <AppShell title={title}>{children}</AppShell>;
}

function AuthRoute() {
  const { user, loading } = useAuth();
  if (loading) return <FullLoader />;
  if (user) return <Navigate to={user.onboarded ? "/" : "/onboarding"} replace />;
  return <Auth />;
}

function OnboardingRoute() {
  const { user, loading } = useAuth();
  if (loading) return <FullLoader />;
  if (!user) return <Navigate to="/auth" replace />;
  if (user.onboarded) return <Navigate to="/" replace />;
  return <Onboarding />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/auth" element={<AuthRoute />} />
          <Route path="/auth/google" element={<GoogleCallback />} />
          <Route path="/onboarding" element={<OnboardingRoute />} />
          <Route path="/" element={<Protected title="Kaelra"><Kaelra /></Protected>} />
          <Route path="/dashboard" element={<Protected title="Dashboard"><Today /></Protected>} />
          <Route path="/talk" element={<Protected title="Talk to Kaelra"><Talk /></Protected>} />
          <Route path="/queue" element={<Protected title="Action Queue"><ActionQueue /></Protected>} />
          <Route path="/memory" element={<Protected title="Memory"><Memory /></Protected>} />
          <Route path="/files" element={<Protected title="Files"><Files /></Protected>} />
          <Route path="/jobs" element={<Protected title="Jobs & Career"><Jobs /></Protected>} />
          <Route path="/class" element={<Protected title="Class & School"><ClassSkill /></Protected>} />
          <Route path="/founder" element={<Protected title="Founder Workspace"><Founder /></Protected>} />
          <Route path="/home" element={<Protected title="Smart Home"><SmartHome /></Protected>} />
          <Route path="/routines" element={<Protected title="Routines"><Routines /></Protected>} />
          <Route path="/accounts" element={<Protected title="Connected Accounts"><ConnectedAccounts /></Protected>} />
          <Route path="/devices" element={<Protected title="Devices"><Devices /></Protected>} />
          <Route path="/settings" element={<Protected title="Settings & Privacy"><Settings /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="top-right" />
    </AuthProvider>
  );
}

export default App;
