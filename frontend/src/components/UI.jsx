import { AlertCircle, LoaderCircle, RefreshCw, X } from "lucide-react";

export function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </div>
  );
}

export function LoadingState({ label = "Loading your care information…" }) {
  return (
    <div className="state-card" role="status">
      <LoaderCircle className="spin" size={22} />
      <span className="loading-copy">{label}<span className="loading-skeleton-bar" aria-hidden="true" /></span>
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="state-card state-error" role="alert">
      <AlertCircle size={21} />
      <div><strong>We couldn’t load this view.</strong><span>{error}</span></div>
      {onRetry && (
        <button className="icon-button" onClick={onRetry} aria-label="Retry">
          <RefreshCw size={17} />
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="empty-state">
      {Icon && <span className="empty-icon"><Icon size={21} /></span>}
      <strong>{title}</strong>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function Modal({ title, description, onClose, children, wide = false }) {
  return (
    <div className="modal-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section
        className={`modal-card${wide ? " modal-wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="modal-heading">
          <div>
            <h2 id="modal-title">{title}</h2>
            {description && <p>{description}</p>}
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={19} />
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}

export function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}

export function StatusPill({ children, tone = "neutral" }) {
  return <span className={`status-pill pill-${tone}`}>{children}</span>;
}

export function FormError({ children }) {
  return children ? <div className="form-error" role="alert">{children}</div> : null;
}
