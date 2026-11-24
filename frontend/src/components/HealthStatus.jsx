const statusStyles = {
  checking: "bg-amber-50 text-amber-800 ring-amber-200",
  ok: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  unavailable: "bg-rose-50 text-rose-800 ring-rose-200",
};

const statusLabels = {
  checking: "Checking backend",
  ok: "Backend connected",
  unavailable: "Backend unavailable",
};

export default function HealthStatus({ status, error, compact = false }) {
  if (compact) {
    return (
      <div className={`health-compact health-${status}`} role="status">
        <span className="health-dot" />
        {status === "ok" ? "Services connected" : status === "checking" ? "Checking connection" : "Backend unavailable"}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-start gap-2">
      <span
        className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium ring-1 ring-inset ${statusStyles[status]}`}
        role="status"
      >
        <span className="h-2 w-2 rounded-full bg-current" aria-hidden="true" />
        {statusLabels[status]}
      </span>
      {error && <p className="text-sm text-rose-700">{error}</p>}
    </div>
  );
}
