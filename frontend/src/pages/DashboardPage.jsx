import { useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowRight,
  CalendarDays,
  Check,
  CheckCircle2,
  Clock3,
  Pill,
  RefreshCw,
  ShieldCheck,
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
  PageHeader,
  StatusPill,
} from "../components/UI.jsx";
import { useToast } from "../components/Toast.jsx"; 

const chartColors = ["#18766f", "#5473ad", "#d3914d", "#8d6ab1", "#4296a1"];
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

  if (!availableForecasts.length) {
    return <EmptyState title="Forecasts unavailable" description="Add a valid medicine schedule to see projected stock coverage." />;
  }

  return (
    <div className="chart-wrap" aria-label="Seven-day projected medicine stock coverage">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="#e9efed" strokeDasharray="4 5" vertical={false} />
          <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fill: "#82918e", fontSize: 11 }} />
          <YAxis domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fill: "#82918e", fontSize: 11 }} tickFormatter={(value) => `${value}%`} />
          <Tooltip
            formatter={(value, name) => [`${Number(value).toFixed(0)}%`, name]}
            labelStyle={{ color: "#203532", fontWeight: 700 }}
            contentStyle={{ border: "1px solid #e6eeeb", borderRadius: 12, boxShadow: "0 10px 24px #172f2b12" }}
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
    return <EmptyState icon={CheckCircle2} title="Nothing scheduled today" description="Your family's medication schedule is clear for now." />;
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
  const toast = useToast();
  const { data, loading, error, refresh } = useLoadData(dashboardData, []);
  const [busyDose, setBusyDose] = useState(null);
  const [mutationError, setMutationError] = useState("");

  async function confirmDose(doseId) {
    setBusyDose(doseId);
    setMutationError("");
    try {
      await api.logDose(doseId, "confirmed");
      toast("Dose confirmed");
      await refresh();
    } catch (requestError) {
      setMutationError(requestError.message);
      toast(requestError.message, "error");
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
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning, family" : hour < 18 ? "Good afternoon, family" : "Good evening, family";
  const dateLabel = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" }).format(new Date());

  return (
    <>
      <PageHeader
        eyebrow={dateLabel.toUpperCase()}
        title={greeting}
        description="Here’s a clear view of the care your family is coordinating."
        actions={<button className="button button-quiet" onClick={refresh}><RefreshCw size={15} /> Refresh</button>}
      />
      {loading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refresh} />}
      {data && (
        <>
          <div className="welcome-strip">
            <div className="welcome-icon"><Sparkles size={20} /></div>
            <div><strong>Small moments make a big difference.</strong><span>Your shared care plan is up to date with the latest family activity.</span></div>
            <ShieldCheck className="welcome-shield" size={22} />
          </div>
          <section className="metric-grid" aria-label="Care overview metrics">
            <Metric icon={Pill} label="Medicines tracked" value={overview.total_medicine_count} hint="In your care plan" tone="teal" />
            <Metric icon={CheckCircle2} label="Doses confirmed" value={overview.confirmed_doses_today} hint="Today" tone="green" />
            <Metric icon={Clock3} label="Awaiting confirmation" value={overview.pending_doses_today} hint="Today's schedule" tone="amber" />
            <Metric icon={CalendarDays} label="Upcoming visits" value={overview.upcoming_appointment_count} hint={`${overview.low_stock_medicine_count} low-stock medicines`} tone="blue" />
          </section>
          {mutationError && <div className="inline-error" role="alert">{mutationError}</div>}
          <div className="dashboard-grid">
            <section className="surface-card dashboard-timeline">
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
            <section className="surface-card alert-card">
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
              ) : (
                <EmptyState title="All clear for now" description="No medicines are currently approaching their refill threshold." />
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
              ) : <EmptyState title="No upcoming appointments" description="Visits added to the family calendar appear here." />}
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
    </>
  );
}

function Metric({ icon: Icon, label, value, hint, tone }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon metric-${tone}`}><Icon size={18} /></div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value ?? "—"}</div>
      <div className="metric-hint">{hint}</div>
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
