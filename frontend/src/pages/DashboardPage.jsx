import { useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowRight,
  CalendarDays,
  Check,
  CheckCircle2,
  Clock3,
  Pill,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";
import { api } from "../services/api.js";
import useLoadData from "../hooks/useLoadData.js";
import { formatDateTime, formatRelative, formatTime } from "../utils/format.js";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusPill,
} from "../components/UI.jsx";

const chartColors = ["#145C4A", "#167C70", "#386F5D", "#4F7584", "#6C8F72"];
const initialsDate = (date) => new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(date);
const itemsOf = (page) => page?.items ?? [];

function dashboardData() {
  return Promise.all([
    api.dashboard(),
    api.medicines(),
    api.dosesToday(),
    api.refillForecasts(),
    api.appointments(),
  ]).then(([overview, medicinesPage, dosesPage, forecastPage, appointmentsPage]) => ({
    overview,
    medicines: itemsOf(medicinesPage),
    doses: itemsOf(dosesPage),
    forecasts: itemsOf(forecastPage),
    appointments: itemsOf(appointmentsPage),
  }));
}

function StockForecastChart({ forecasts }) {
  const availableForecasts = forecasts.filter((item) => item.forecast_available);
  const data = useMemo(() => {
    const now = new Date();
    const days = Array.from({ length: 7 }, (_, index) => {
      const date = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + index));
      return {
        key: date.toISOString().slice(0, 10),
        day: initialsDate(date),
        ...Object.fromEntries(availableForecasts.map((forecast) => [String(forecast.medicine_id), 100])),
      };
    });

    availableForecasts.forEach((forecast) => {
      const current = Number(forecast.current_available_stock || 0);
      let consumed = 0;
      const perDay = new Map();
      forecast.upcoming_scheduled_doses.forEach((dose) => {
        const key = new Date(dose.expected_at).toISOString().slice(0, 10);
        perDay.set(key, (perDay.get(key) || 0) + Number(dose.units || 0));
      });
      days.forEach((day) => {
        consumed += perDay.get(day.key) || 0;
        day[String(forecast.medicine_id)] =
          current > 0 ? Math.max(0, ((current - consumed) / current) * 100) : 0;
      });
    });
    return days;
  }, [availableForecasts]);

  if (!forecasts.length) {
    return (
      <EmptyState
        icon={Pill}
        title="No medicines to forecast yet"
        description="Add a medicine to see its projected stock coverage here."
        action={<Link className="text-link" to="/medicines">Add a medicine <ArrowRight size={14} /></Link>}
      />
    );
  }

  if (!availableForecasts.length) {
    return <EmptyState title="Schedules need a quick review" description="Check the medicine schedules to make stock coverage available." />;
  }

  return (
    <div className="chart-wrap" aria-label="Seven-day projected medicine stock coverage">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="#E2E3D9" strokeDasharray="4 5" vertical={false} />
          <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fill: "#697A75", fontSize: 11 }} />
          <YAxis domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fill: "#697A75", fontSize: 11 }} tickFormatter={(value) => `${value}%`} />
          <Tooltip
            formatter={(value, name) => [`${Number(value).toFixed(0)}%`, name]}
            labelStyle={{ color: "#183D32", fontWeight: 700 }}
            contentStyle={{ border: "1px solid #E2E3D9", borderRadius: 12, background: "#FFFEFA", color: "#183D32", boxShadow: "0 10px 24px rgb(24 61 50 / 12%)" }}
          />
          {availableForecasts.map((forecast, index) => (
            <Line
              key={forecast.medicine_id}
              type="monotone"
              dataKey={String(forecast.medicine_id)}
              name={forecast.medicine_name}
              stroke={chartColors[index % chartColors.length]}
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function DoseTimeline({ doses, medicines, onConfirm, busyDose }) {
  const medicineById = new Map(medicines.map((medicine) => [medicine.id, medicine]));
  const sorted = [...doses].sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));

  if (!sorted.length) {
    return (
      <EmptyState
        icon={CheckCircle2}
        title="Nothing scheduled today"
        description="Your family's medication schedule is clear for now."
        action={<Link className="text-link" to="/medicines">Review medicines <ArrowRight size={14} /></Link>}
      />
    );
  }

  return (
    <div className="timeline-list">
      {sorted.map((dose) => {
        const medicine = medicineById.get(dose.medicine_id);
        const statusTone = dose.status === "confirmed" ? "success" : dose.status === "skipped" ? "muted" : dose.status === "delayed" ? "warning" : "neutral";
        return (
          <div className="timeline-item" key={dose.id}>
            <div className={`timeline-marker marker-${statusTone}`}>
              {dose.status === "confirmed" ? <Check size={14} /> : <Clock3 size={14} />}
            </div>
            <div className="timeline-time">{formatTime(new Date(dose.scheduled_at).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }))}</div>
            <div className="timeline-details">
              <strong>{medicine?.name || `Medicine #${dose.medicine_id}`}</strong>
              <span>{medicine ? `${medicine.dosage} · ${medicine.units_per_dose} units` : "Dose schedule"}</span>
            </div>
            <div className="timeline-action">
              {dose.status === "pending" || dose.status === "delayed" ? (
                <button className="button button-subtle button-small" disabled={busyDose === dose.id} onClick={() => onConfirm(dose.id)}>
                  <Check size={14} /> {busyDose === dose.id ? "Saving" : "Confirm"}
                </button>
              ) : (
                <StatusPill tone={statusTone}>{dose.status}</StatusPill>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function DashboardPage() {
  const { data, loading, error, refresh } = useLoadData(dashboardData, []);
  const [busyDose, setBusyDose] = useState(null);
  const [mutationError, setMutationError] = useState("");

  async function confirmDose(doseId) {
    setBusyDose(doseId);
    setMutationError("");
    try {
      await api.logDose(doseId, "confirmed");
      await refresh();
    } catch (requestError) {
      setMutationError(requestError.message);
    } finally {
      setBusyDose(null);
    }
  }

  const overview = data?.overview;
  const medicines = data?.medicines || [];
  const forecasts = data?.forecasts || [];
  const appointments = (data?.appointments || [])
    .filter((appointment) => new Date(appointment.appointment_datetime) >= new Date() && ["scheduled", "confirmed"].includes(appointment.status))
    .sort((a, b) => new Date(a.appointment_datetime) - new Date(b.appointment_datetime))
    .slice(0, 3);
  const alerts = forecasts.filter((forecast) => ["CRITICAL", "URGENT", "UPCOMING"].includes(forecast.urgency));
  const hasAvailableForecasts = forecasts.some((forecast) => forecast.forecast_available);
  const dateLabel = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" }).format(new Date());
  const pendingDoseCount = overview?.pending_doses_today;
  const pendingDoseLabel = pendingDoseCount == null
    ? "Dose status unavailable"
    : pendingDoseCount === 0
      ? "Today's doses are up to date"
      : `${pendingDoseCount} dose${pendingDoseCount === 1 ? "" : "s"} to confirm today`;

  return (
    <div className="dashboard-page">
      {loading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refresh} />}
      {data && (
        <>
          <section className="dashboard-hero dashboard-enter" aria-labelledby="dashboard-hero-title">
            <div className="dashboard-hero-copy">
              <span className="dashboard-hero-eyebrow">{dateLabel.toUpperCase()} <i /> YOUR FAMILY CARE SPACE</span>
              <h1 id="dashboard-hero-title">Good care is built together.</h1>
              <p>Keep schedules, refills, and family updates in sync — one thoughtful step at a time.</p>
              <div className="dashboard-hero-actions">
                <Link className="dashboard-hero-action" to="/medicines">Review care plan <ArrowRight size={15} /></Link>
                <span className="dashboard-hero-status">
                  {pendingDoseCount === 0 ? <CheckCircle2 size={15} /> : <Clock3 size={15} />}
                  {pendingDoseLabel}
                </span>
              </div>
            </div>
          </section>
          <section className="dashboard-stat-grid dashboard-enter" aria-label="Care overview">
            <Metric icon={Pill} label="Medicines tracked" value={overview.total_medicine_count} hint="in the shared care plan" tone="green" />
            <Metric icon={CheckCircle2} label="Doses confirmed" value={overview.confirmed_doses_today} hint="today" tone="teal" />
            <Metric icon={Clock3} label="Awaiting confirmation" value={overview.pending_doses_today} hint="today" tone="amber" />
            <Metric icon={CalendarDays} label="Upcoming visits" value={overview.upcoming_appointment_count} hint="on the family calendar" tone="blue" />
          </section>
          {mutationError && <div className="inline-error" role="alert">{mutationError}</div>}
          <div className="dashboard-grid">
            <section className="surface-card dashboard-timeline" id="today-medication">
              <CardHeading title="Today’s medication" subtitle="A shared view of today’s schedule" side={<Link className="text-link" to="/medicines">All medicines <ArrowRight size={14} /></Link>} />
              <DoseTimeline doses={data.doses} medicines={medicines} onConfirm={confirmDose} busyDose={busyDose} />
            </section>
            <section className="surface-card forecast-card">
              <CardHeading title="Stock outlook" subtitle="Projected remaining stock coverage" side={<span className="chart-period">7 days</span>} />
              <StockForecastChart forecasts={forecasts} />
              <div className="forecast-legend">
                {forecasts.filter((item) => item.forecast_available).slice(0, 4).map((forecast, index) => (
                  <span key={forecast.medicine_id}><i style={{ backgroundColor: chartColors[index % chartColors.length] }} />{forecast.medicine_name}</span>
                ))}
              </div>
              <Link className="text-link forecast-link" to="/medicines">View refill forecasts <ArrowRight size={14} /></Link>
            </section>
            <section className={`surface-card alert-card${alerts.length ? " alert-card-active" : ""}`}>
              <CardHeading title="Refill watch" subtitle="Based on upcoming scheduled doses" side={<Link className="text-link" to="/medicines">View all <ArrowRight size={14} /></Link>} />
              {alerts.length ? (
                <div className="compact-list">
                  {alerts.slice(0, 4).map((forecast) => (
                    <Link to="/medicines" className="compact-row" key={forecast.medicine_id}>
                      <span className={`list-icon ${forecast.urgency === "CRITICAL" ? "icon-danger" : "icon-warning"}`}><TriangleAlert size={16} /></span>
                      <span className="compact-copy"><strong>{forecast.medicine_name}</strong><small>{forecast.current_available_stock} units available</small></span>
                      <StatusPill tone={forecast.urgency === "CRITICAL" ? "danger" : "warning"}>{forecast.urgency}</StatusPill>
                    </Link>
                  ))}
                </div>
              ) : !forecasts.length ? (
                <EmptyState
                  icon={Pill}
                  title="No refill forecasts yet"
                  description="Add a medicine to start tracking refill timing."
                  action={<Link className="text-link" to="/medicines">Open medicines <ArrowRight size={14} /></Link>}
                />
              ) : hasAvailableForecasts ? (
                <EmptyState title="No refill alerts right now" description="Current medicine forecasts are above their refill thresholds." />
              ) : (
                <EmptyState title="Forecasts need attention" description="Review medicine schedules to calculate refill urgency." />
              )}
            </section>
            <section className="surface-card appointment-card">
              <CardHeading title="Coming up" subtitle="Your next family care visits" side={<Link className="text-link" to="/calendar">Calendar <ArrowRight size={14} /></Link>} />
              {appointments.length ? (
                <div className="compact-list">
                  {appointments.map((appointment) => (
                    <div className="compact-row" key={appointment.id}>
                      <span className="date-tile"><strong>{new Date(appointment.appointment_datetime).getDate()}</strong><small>{new Date(appointment.appointment_datetime).toLocaleDateString(undefined, { month: "short" })}</small></span>
                      <span className="compact-copy"><strong>{appointment.title}</strong><small>{appointment.doctor_name} · {formatDateTime(appointment.appointment_datetime, { year: undefined })}</small></span>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No upcoming appointments"
                  description="Visits added to the family calendar appear here."
                  action={<Link className="text-link" to="/calendar">Open calendar <ArrowRight size={14} /></Link>}
                />
              )}
            </section>
            <section className="surface-card activity-card">
              <CardHeading title="Family activity" subtitle="Recent updates from your care circle" side={<Link className="text-link" to="/family">See family <ArrowRight size={14} /></Link>} />
              {overview.recent_family_activity.length ? (
                <div className="activity-list">
                  {overview.recent_family_activity.slice(0, 4).map((activity, index) => (
                    <div className="activity-row" key={`${activity.activity_type}-${activity.occurred_at}-${index}`}>
                      <span className={`activity-symbol activity-${activity.activity_type}`}><ActivityIcon type={activity.activity_type} /></span>
                      <span className="compact-copy"><strong>{activity.description}</strong><small>{activity.caregiver_name || "Family update"} · {formatRelative(activity.occurred_at)}</small></span>
                    </div>
                  ))}
                </div>
              ) : <EmptyState title="No recent updates" description="Family actions will appear here as care is coordinated." />}
            </section>
          </div>
        </>
      )}
    </div>
  );
}

function Metric({ icon: Icon, label, value, hint, tone }) {
  return (
    <article className={`care-stat care-stat-${tone}`}>
      <div className="care-stat-label"><Icon size={15} /><span>{label}</span></div>
      <strong className="care-stat-value">{value ?? "—"}</strong>
      <span className="care-stat-hint">{hint}</span>
    </article>
  );
}

function CardHeading({ title, subtitle, side }) {
  return <div className="card-heading"><div><h2>{title}</h2><p>{subtitle}</p></div>{side}</div>;
}

function ActivityIcon({ type }) {
  if (type === "dose") return <CheckCircle2 size={15} />;
  if (type === "appointment") return <CalendarDays size={15} />;
  if (type === "stock_transaction") return <ArrowDownRight size={15} />;
  return <Sparkles size={15} />;
}
