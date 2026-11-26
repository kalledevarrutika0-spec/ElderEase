import { Link, NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  CalendarDays,
  HeartHandshake,
  LayoutDashboard,
  LogOut,
  MessageCircle,
  Pill,
  Plus,
} from "lucide-react";
import HealthStatus from "./HealthStatus.jsx";
import useHealthStatus from "../hooks/useHealthStatus.js";
import { useAuth } from "../context/AuthContext.jsx";
const links = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/medicines", label: "Medications", icon: Pill },
  { to: "/calendar", label: "Care calendar", icon: CalendarDays },
  { to: "/family", label: "Family", icon: HeartHandshake },
  { to: "/assistant", label: "AI assistant", icon: MessageCircle },
];

function Navigation({ mobile = false }) {
  return (
    <nav
      aria-label={mobile ? "Mobile navigation" : "Main navigation"}
      className={mobile ? "mobile-nav" : "sidebar-nav"}
    >
      {links.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `nav-link${isActive ? " nav-link-active" : ""}`
          }
        >
          <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default function AppShell() {
  const health = useHealthStatus();
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand-lockup" to="/" aria-label="Elderease overview">
          <span className="brand-mark"><Activity size={21} /></span>
          <span>
            <strong>Elderease</strong>
            <small>Care, together</small>
          </span>
        </Link>
        <div className="workspace-label">WORKSPACE</div>
        <Navigation />
        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <div className="help-icon"><HeartHandshake size={18} /></div>
            <p>Care is a team effort.</p>
            <span>Keep everyone in the loop.</span>
          </div>
          <HealthStatus status={health.status} error={health.error} compact />
          <div className="sidebar-version">ELDEREASE · FAMILY CARE</div>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="topbar-context">
            <span className="status-dot" />
            <span>Your family care space</span>
          </div>
          <div className="topbar-actions">
            <span className="privacy-chip">Hi, {user?.name}</span>
            <NavLink className="button button-primary topbar-cta" to="/medicines">
              <Plus size={16} /> Add care detail
            </NavLink>
            <button className="button button-quiet topbar-cta" onClick={logout}>
              <LogOut size={15} /> Log out
            </button>
          </div>
        </header>
        <main className="page-content"><Outlet /></main>
      </div>
      <Navigation mobile />
    </div>
  );
}
