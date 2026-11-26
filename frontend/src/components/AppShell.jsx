import { Link, NavLink, Outlet } from "react-router-dom";
import {
  CalendarDays,
  HeartHandshake,
  LayoutDashboard,
  Leaf,
  LockKeyhole,
  MessageCircle,
  Pill,
  Plus,
  UsersRound,
} from "lucide-react";
import HealthStatus from "./HealthStatus.jsx";
import useHealthStatus from "../hooks/useHealthStatus.js";
import { useAuth } from "../context/AuthContext.jsx";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/medicines", label: "Medicines", icon: Pill },
  { to: "/calendar", label: "Calendar", icon: CalendarDays },
  { to: "/family", label: "Family", icon: HeartHandshake },
  { to: "/assistant", label: "AI Assistant", icon: MessageCircle },
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
          <span className="brand-mark"><Leaf size={21} strokeWidth={1.8} /></span>
          <span>
            <strong>Elderease</strong>
            <small>Care, together</small>
          </span>
        </Link>
        <div className="workspace-switcher" aria-label="Current family workspace">
          <span className="workspace-switcher-icon"><UsersRound size={17} /></span>
          <span><small>SHARED CARE SPACE</small><strong>Family workspace</strong></span>
        </div>
        <div className="workspace-label">YOUR CARE</div>
        <Navigation />
        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <div className="help-icon"><HeartHandshake size={18} /></div>
            <p>Care, shared with care.</p>
            <span>Every small update helps your circle.</span>
          </div>
          <HealthStatus status={health.status} error={health.error} compact />
          <div className="sidebar-version"><span /> ELDEREASE · FAMILY CARE</div>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="topbar-context">
            <span className="status-dot" />
            <span>Your family care space</span>
          </div>
          <div className="topbar-actions">
            <span className="privacy-chip"><LockKeyhole size={13} /> Private family workspace</span>
            {user?.email && <span className="topbar-user">{user.email}</span>}
            <NavLink className="button button-primary topbar-cta" to="/medicines">
              <Plus size={16} /> Add medicine
            </NavLink>
            <button className="button button-quiet topbar-cta" type="button" onClick={logout}>
              Log out
            </button>
          </div>
        </header>
        <main className="page-content"><Outlet /></main>
      </div>
      <Navigation mobile />
    </div>
  );
}
