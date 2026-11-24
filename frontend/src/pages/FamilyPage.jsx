import { useState } from "react";
import {
  Bell,
  Check,
  CheckCheck,
  HeartHandshake,
  Mail,
  Phone,
  RefreshCw,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { api } from "../services/api.js";
import useLoadData from "../hooks/useLoadData.js";
import { formatDateTime, formatRelative, initials } from "../utils/format.js";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusPill,
} from "../components/UI.jsx";

const itemsOf = (page) => page?.items ?? [];

function loadFamily() {
  return Promise.all([
    api.caregivers(),
    api.medicines(),
    api.appointments(),
    api.notifications(),
    api.dashboard(),
  ]).then(([caregivers, medicines, appointments, notifications, dashboard]) => ({
    caregivers: itemsOf(caregivers),
    medicines: itemsOf(medicines),
    appointments: itemsOf(appointments),
    notifications: itemsOf(notifications),
    activity: dashboard.recent_family_activity,
  }));
}

export default function FamilyPage() {
  const { data, loading, error, refresh } = useLoadData(loadFamily, []);
  const [busyNotification, setBusyNotification] = useState(null);
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const caregivers = data?.caregivers || [];
  const notifications = data?.notifications || [];

  async function acknowledge(notificationId) {
    setBusyNotification(notificationId);
    setActionError("");
    try {
      await api.acknowledgeNotification(notificationId);
      setNotice("Notification acknowledged.");
      await refresh();
    } catch (requestError) {
      setActionError(requestError.message);
    } finally {
      setBusyNotification(null);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="YOUR CARE CIRCLE"
        title="Family coordination"
        description="See who’s helping, what they’re coordinating, and the latest shared updates."
        actions={<button className="button button-quiet" onClick={refresh}><RefreshCw size={15} /> Refresh</button>}
      />
      {notice && <div className="success-banner"><Check size={16} />{notice}<button onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}
      {actionError && <div className="inline-error" role="alert">{actionError}</div>}
      {loading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refresh} />}
      {data && (
        <>
          <div className="family-summary">
            <div className="summary-icon"><HeartHandshake size={20} /></div>
            <div><strong>{caregivers.length} {caregivers.length === 1 ? "caregiver" : "caregivers"} in your circle</strong><span>Caregiver records and responsibilities are shared across this family workspace.</span></div>
            <ShieldCheck size={20} className="summary-shield" />
          </div>
          {caregivers.length ? (
            <div className="caregiver-grid">
              {caregivers.map((caregiver, index) => {
                const assignedMedicines = data.medicines.filter((medicine) => medicine.assigned_caregiver_id === caregiver.id);
                const assignedAppointments = data.appointments.filter((appointment) => appointment.assigned_caregiver_id === caregiver.id);
                return (
                  <article className="surface-card caregiver-card" key={caregiver.id}>
                    <div className="caregiver-card-top">
                      <div className={`caregiver-avatar avatar-${index % 4}`}>{initials(caregiver.name)}</div>
                      <span className="caregiver-role">{caregiver.relationship}</span>
                    </div>
                    <h2>{caregiver.name}</h2>
                    <div className="caregiver-contact">
                      {caregiver.email && <span><Mail size={14} />{caregiver.email}</span>}
                      {caregiver.phone && <span><Phone size={14} />{caregiver.phone}</span>}
                      {!caregiver.email && !caregiver.phone && <span className="muted-copy">No contact details shared</span>}
                    </div>
                    <div className="responsibility-block">
                      <h3>Care responsibilities</h3>
                      <div className="responsibility-stats">
                        <div><strong>{assignedMedicines.length}</strong><span>medicines</span></div>
                        <div><strong>{assignedAppointments.length}</strong><span>appointments</span></div>
                      </div>
                      {(assignedMedicines.length > 0 || assignedAppointments.length > 0) ? (
                        <ul>
                          {assignedMedicines.slice(0, 3).map((medicine) => <li key={`m-${medicine.id}`}>{medicine.name}</li>)}
                          {assignedAppointments.slice(0, 2).map((appointment) => <li key={`a-${appointment.id}`}>{appointment.title}</li>)}
                        </ul>
                      ) : <p className="muted-copy">No items assigned yet.</p>}
                    </div>
                  </article>
                );
              })}
            </div>
          ) : <EmptyState icon={UserRound} title="Your care circle is ready to grow" description="Caregiver profiles will appear here when available." />}

          <div className="family-lower-grid">
            <section className="surface-card">
              <div className="card-heading"><div><h2>Recent family activity</h2><p>Updates from the shared care plan</p></div><span className="subtle-count">{data.activity.length} updates</span></div>
              {data.activity.length ? (
                <div className="family-activity-list">
                  {data.activity.map((activity, index) => (
                    <div className="family-activity-row" key={`${activity.activity_type}-${activity.occurred_at}-${index}`}>
                      <span className={`activity-symbol activity-${activity.activity_type}`}><ActivityGlyph type={activity.activity_type} /></span>
                      <span className="compact-copy"><strong>{activity.description}</strong><small>{activity.caregiver_name || "Family update"} · {formatDateTime(activity.occurred_at)}</small></span>
                      <time>{formatRelative(activity.occurred_at)}</time>
                    </div>
                  ))}
                </div>
              ) : <EmptyState title="No activity yet" description="Shared dose, stock, and appointment updates will appear here." />}
            </section>
            <section className="surface-card">
              <div className="card-heading"><div><h2>Notifications</h2><p>Keep shared reminders acknowledged</p></div><Bell size={18} className="heading-icon" /></div>
              {notifications.length ? (
                <div className="notification-list">
                  {notifications.map((notification) => (
                    <div className={`notification-row${notification.status === "acknowledged" ? " notification-done" : ""}`} key={notification.id}>
                      <span className="notification-symbol"><Bell size={15} /></span>
                      <div className="notification-copy"><strong>{notification.message}</strong><small>{notification.notification_type.replaceAll("_", " ")} · {formatRelative(notification.created_at)}</small></div>
                      {notification.status === "acknowledged" ? <StatusPill tone="success"><CheckCheck size={12} /> Seen</StatusPill> : notification.status === "failed" ? <StatusPill tone="danger">Failed</StatusPill> : <button className="button button-subtle button-small" disabled={busyNotification === notification.id} onClick={() => acknowledge(notification.id)}>{busyNotification === notification.id ? "Saving…" : "Acknowledge"}</button>}
                    </div>
                  ))}
                </div>
              ) : <EmptyState icon={Bell} title="No notifications" description="Family notifications will show up here." />}
            </section>
          </div>
        </>
      )}
    </>
  );
}

function ActivityGlyph({ type }) {
  if (type === "dose") return <CheckCheck size={15} />;
  if (type === "appointment") return <span className="activity-letter">A</span>;
  if (type === "stock_transaction") return <span className="activity-letter">S</span>;
  return <Bell size={15} />;
}
