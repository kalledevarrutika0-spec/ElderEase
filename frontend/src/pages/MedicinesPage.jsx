import { useEffect, useState } from "react";
import {
  ArrowDownToLine,
  ArrowUpRight,
  CalendarClock,
  Check,
  Clock3,
  History,
  PackagePlus,
  Pencil,
  Pill,
  Plus,
  RefreshCw,
  TriangleAlert,
} from "lucide-react";
import { api } from "../services/api.js";
import useLoadData from "../hooks/useLoadData.js";
import { formatDateTime, formatTime } from "../utils/format.js";
import {
  EmptyState,
  ErrorState,
  Field,
  FormError,
  LoadingState,
  Modal,
  PageHeader,
  StatusPill,
} from "../components/UI.jsx";

const itemsOf = (page) => page?.items ?? [];
const initialForm = {
  name: "",
  dosage: "",
  units_per_dose: "1",
  frequency_per_day: "1",
  scheduled_times: "08:00",
  current_stock: "0",
  refill_threshold: "5",
  assigned_caregiver_id: "",
  instructions: "",
};

function loadMedicines() {
  return Promise.all([
    api.medicines(),
    api.refillForecasts(),
    api.dosesToday(),
    api.caregivers(),
  ]).then(([medicines, forecasts, doses, caregivers]) => ({
    medicines: itemsOf(medicines),
    forecasts: itemsOf(forecasts),
    doses: itemsOf(doses),
    caregivers: itemsOf(caregivers),
  }));
}

export default function MedicinesPage() {
  const { data, loading, error, refresh } = useLoadData(loadMedicines, []);
  const [dialog, setDialog] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState("");
  const [busyDose, setBusyDose] = useState(null);
  const medicines = data?.medicines || [];
  const caregivers = data?.caregivers || [];
  const forecasts = data?.forecasts || [];
  const doses = data?.doses || [];
  const forecastById = new Map(forecasts.map((item) => [item.medicine_id, item]));
  const medicineById = new Map(medicines.map((item) => [item.id, item]));

  function openMedicine(medicine = null) {
    setFormError("");
    setSuccess("");
    setDialog({
      type: "medicine",
      medicine,
      form: medicine
        ? {
            name: medicine.name,
            dosage: medicine.dosage,
            units_per_dose: String(medicine.units_per_dose),
            frequency_per_day: String(medicine.frequency_per_day),
            scheduled_times: medicine.scheduled_times.join(", "),
            current_stock: String(medicine.current_stock),
            refill_threshold: String(medicine.refill_threshold),
            assigned_caregiver_id: medicine.assigned_caregiver_id ? String(medicine.assigned_caregiver_id) : "",
            instructions: medicine.instructions || "",
          }
        : { ...initialForm },
    });
  }

  async function saveMedicine(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const source = dialog.form;
    const scheduledTimes = source.scheduled_times
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
    const frequency = Number(source.frequency_per_day);
    if (scheduledTimes.length !== frequency) {
      setFormError("Add one scheduled time for each daily dose.");
      return;
    }
    if (new Set(scheduledTimes).size !== scheduledTimes.length) {
      setFormError("Scheduled times must be unique.");
      return;
    }
    const payload = {
      name: source.name.trim(),
      dosage: source.dosage.trim(),
      units_per_dose: source.units_per_dose,
      frequency_per_day: frequency,
      scheduled_times: scheduledTimes,
      refill_threshold: source.refill_threshold,
      assigned_caregiver_id: source.assigned_caregiver_id ? Number(source.assigned_caregiver_id) : null,
      instructions: source.instructions.trim() || null,
    };
    if (!dialog.medicine) {
      payload.current_stock = source.current_stock;
      if (Number(payload.current_stock) > 0 && !payload.assigned_caregiver_id) {
        setFormError("Choose a caregiver to audit opening stock.");
        return;
      }
    }
    setSaving(true);
    setFormError("");
    try {
      if (dialog.medicine) await api.updateMedicine(dialog.medicine.id, payload);
      else await api.createMedicine(payload);
      setDialog(null);
      setSuccess(dialog.medicine ? "Medicine details updated." : "Medicine added to the care plan.");
      await refresh();
    } catch (requestError) {
      setFormError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function confirmDose(doseId) {
    setBusyDose(doseId);
    setFormError("");
    try {
      await api.logDose(doseId, "confirmed");
      setSuccess("Dose confirmation saved and stock updated.");
      await refresh();
    } catch (requestError) {
      setFormError(requestError.message);
    } finally {
      setBusyDose(null);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="MEDICATION PLAN"
        title="Medication care"
        description="Keep schedules, stock, and refill timing visible to the whole family."
        actions={<button className="button button-primary" onClick={() => openMedicine()}><Plus size={16} /> Add medicine</button>}
      />
      {success && <div className="success-banner"><Check size={16} />{success}<button onClick={() => setSuccess("")} aria-label="Dismiss">×</button></div>}
      {formError && !dialog && <div className="inline-error" role="alert">{formError}</div>}
      {loading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refresh} />}
      {data && (
        <>
          <div className="section-intro">
            <div><strong>{medicines.length} medicines</strong><span>Stock balances reflect recorded purchases, corrections, and confirmed doses.</span></div>
            <button className="button button-quiet" onClick={refresh}><RefreshCw size={15} /> Refresh</button>
          </div>
          {medicines.length ? (
            <div className="medicine-grid">
              {medicines.map((medicine) => (
                <MedicineCard
                  key={medicine.id}
                  medicine={medicine}
                  forecast={forecastById.get(medicine.id)}
                  caregiver={caregivers.find((person) => person.id === medicine.assigned_caregiver_id)}
                  onEdit={() => openMedicine(medicine)}
                  onStock={() => setDialog({ type: "stock", medicine })}
                />
              ))}
            </div>
          ) : (
            <EmptyState icon={Pill} title="No medicines added yet" description="Add a medicine to make schedules and refill forecasts visible to your family." action={<button className="button button-primary" onClick={() => openMedicine()}><Plus size={16} /> Add a medicine</button>} />
          )}
          <section className="surface-card dose-section">
            <div className="card-heading"><div><h2>Today’s dose confirmations</h2><p>Confirm a dose only after it has been taken.</p></div><StatusPill>{doses.filter((dose) => dose.status === "pending").length} pending</StatusPill></div>
            {doses.length ? (
              <div className="table-scroll">
                <table className="data-table">
                  <thead><tr><th>Medicine</th><th>Scheduled</th><th>Caregiver</th><th>Status</th><th /></tr></thead>
                  <tbody>
                    {[...doses].sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at)).map((dose) => {
                      const medicine = medicineById.get(dose.medicine_id);
                      const caregiver = caregivers.find((person) => person.id === dose.caregiver_id);
                      return (
                        <tr key={dose.id}>
                          <td><strong>{medicine?.name || `Medicine #${dose.medicine_id}`}</strong><small>{medicine?.dosage || "Scheduled dose"}</small></td>
                          <td>{formatDateTime(dose.scheduled_at, { year: undefined })}</td>
                          <td>{caregiver?.name || "Caregiver"}</td>
                          <td><StatusPill tone={dose.status === "confirmed" ? "success" : dose.status === "skipped" ? "muted" : dose.status === "delayed" ? "warning" : "neutral"}>{dose.status}</StatusPill></td>
                          <td className="table-actions">{["pending", "delayed"].includes(dose.status) && <button className="button button-subtle button-small" disabled={busyDose === dose.id} onClick={() => confirmDose(dose.id)}><Check size={14} /> Confirm taken</button>}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState icon={CalendarClock} title="No doses scheduled today" description="Today’s dose log is empty." />}
          </section>
        </>
      )}
      {dialog?.type === "medicine" && (
        <Modal
          title={dialog.medicine ? "Edit medicine" : "Add a medicine"}
          description="Use the prescribed schedule and dosage provided by the care team."
          onClose={() => setDialog(null)}
          wide
        >
          <form className="form-grid" onSubmit={saveMedicine}>
            <Field label="Medicine name"><input required maxLength={120} value={dialog.form.name} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="name" placeholder="e.g. Morning medication" /></Field>
            <Field label="Prescribed dosage"><input required maxLength={80} value={dialog.form.dosage} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="dosage" placeholder="e.g. 1 tablet" /></Field>
            <Field label="Units per dose"><input required type="number" min="0.001" step="0.001" value={dialog.form.units_per_dose} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="units_per_dose" /></Field>
            <Field label="Doses per day"><input required type="number" min="1" max="24" step="1" value={dialog.form.frequency_per_day} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="frequency_per_day" /></Field>
            <Field label="Scheduled times" hint="Use 24-hour HH:MM; separate multiple times with commas.">
              <input required value={dialog.form.scheduled_times} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="scheduled_times" placeholder="08:00, 20:00" />
            </Field>
            <Field label="Refill threshold"><input required type="number" min="0" step="0.001" value={dialog.form.refill_threshold} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="refill_threshold" /></Field>
            {!dialog.medicine && <Field label="Opening stock"><input required type="number" min="0" step="0.001" value={dialog.form.current_stock} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="current_stock" /></Field>}
            <Field label="Responsible caregiver">
              <select value={dialog.form.assigned_caregiver_id} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="assigned_caregiver_id">
                <option value="">Not assigned</option>
                {caregivers.map((person) => <option key={person.id} value={person.id}>{person.name} · {person.relationship}</option>)}
              </select>
            </Field>
            <Field label="Care instructions"><textarea rows="3" maxLength={4000} value={dialog.form.instructions} onChange={(event) => updateForm(setDialog, event.target.name, event.target.value)} name="instructions" placeholder="Optional notes from the care plan" /></Field>
            <div className="form-footer"><FormError>{formError}</FormError><button className="button button-quiet" type="button" onClick={() => setDialog(null)}>Cancel</button><button className="button button-primary" disabled={saving}>{saving ? "Saving…" : dialog.medicine ? "Save changes" : "Add medicine"}</button></div>
          </form>
        </Modal>
      )}
      {dialog?.type === "stock" && (
        <StockDialog
          medicine={dialog.medicine}
          caregivers={caregivers}
          onClose={() => setDialog(null)}
          onSaved={async () => { setDialog(null); setSuccess("Stock transaction recorded."); await refresh(); }}
        />
      )}
    </>
  );
}

function updateForm(setDialog, name, value) {
  setDialog((current) => ({ ...current, form: { ...current.form, [name]: value } }));
}

function MedicineCard({ medicine, forecast, caregiver, onEdit, onStock }) {
  const urgency = forecast?.urgency;
  const tone = !forecast?.forecast_available
    ? "muted"
    : urgency === "CRITICAL"
      ? "danger"
      : ["URGENT", "UPCOMING"].includes(urgency)
        ? "warning"
        : "success";
  const stock = Number(medicine.current_stock);
  const threshold = Number(medicine.refill_threshold);
  const fill = threshold > 0 ? Math.min(100, (stock / (threshold * 2)) * 100) : stock > 0 ? 100 : 0;
  const schedule = (medicine.scheduled_times || []).map(formatTime).join(" · ");

  return (
    <article className={`surface-card medicine-card medicine-card-${tone}`}>
      <div className="medicine-card-top">
        <div className="medicine-illustration" aria-hidden="true">
          <svg viewBox="0 0 146 82" role="presentation">
            <rect x="1" y="1" width="144" height="80" rx="14" fill="var(--surface)" />
            <circle cx="119" cy="18" r="13" fill="var(--surface-raised)" />
            <path d="M82 69c13-19 35-24 59-16v27H82V69Z" fill="#E0E9DE" />
            <rect x="23" y="29" width="31" height="39" rx="7" fill="#D6E4D6" stroke="#9BB7A3" strokeWidth="1.5" />
            <rect x="29" y="21" width="19" height="10" rx="3" fill="#B7CEBC" />
            <rect x="28" y="42" width="21" height="13" rx="3" fill="var(--surface-raised)" />
            <path d="M33 48.5h11" stroke="#167C70" strokeWidth="2" strokeLinecap="round" />
            <g transform="rotate(-27 78 46)">
              <rect x="62" y="39" width="33" height="14" rx="7" fill="#D8B875" />
              <path d="M78.5 39v14" stroke="#FFFEFA" strokeWidth="1.5" />
              <path d="M64 46h13" stroke="#F7E8C8" strokeWidth="1" />
            </g>
            <rect x="105" y="31" width="25" height="36" rx="8" fill="#DDE9E2" stroke="#9DBEB1" strokeWidth="1.5" />
            <circle cx="113" cy="41" r="3" fill="#167C70" stroke="#F7F5EF" />
            <circle cx="122" cy="41" r="3" fill="#167C70" stroke="#F7F5EF" />
            <circle cx="113" cy="51" r="3" fill="#167C70" stroke="#F7F5EF" />
            <circle cx="122" cy="51" r="3" fill="#167C70" stroke="#F7F5EF" />
            <circle cx="113" cy="60" r="3" fill="#167C70" stroke="#F7F5EF" />
            <circle cx="122" cy="60" r="3" fill="#167C70" stroke="#F7F5EF" />
          </svg>
        </div>
        <button className="icon-button" onClick={onEdit} aria-label={`Edit ${medicine.name}`}><Pencil size={16} /></button>
      </div>
      <div className="medicine-title-row"><div><h2>{medicine.name}</h2><p>{medicine.dosage}</p></div><StatusPill tone={tone}>{urgency || "NO FORECAST"}</StatusPill></div>
      <div className="medicine-schedule"><Clock3 size={15} />{medicine.frequency_per_day}× daily <span>·</span> {schedule || "No schedule"}</div>
      <div className="stock-summary">
        <div><span>Available stock</span><strong>{medicine.current_stock} <small>units</small></strong></div>
        <div className="stock-meter" aria-label={`${medicine.current_stock} units in stock`}><i style={{ width: `${fill}%` }} className={stock <= threshold ? "meter-low" : ""} /></div>
        <div className="stock-caption"><span>Refill at {medicine.refill_threshold}</span>{caregiver && <span>Managed by {caregiver.name}</span>}</div>
      </div>
      {forecast?.forecast_available ? (
        <div className="forecast-summary">
          <div><CalendarClock size={15} /><span>Est. depletion</span><strong>{formatDateTime(forecast.estimated_depletion_at)}</strong></div>
          <div><ArrowDownToLine size={15} /><span>7-day use</span><strong>{forecast.expected_consumption} units</strong></div>
        </div>
      ) : (
        <div className="forecast-unavailable"><TriangleAlert size={15} />{forecast?.data_warnings?.[0] || "Forecast unavailable"}</div>
      )}
      <div className="medicine-card-footer">
        <span className="caregiver-caption">{caregiver ? `${caregiver.relationship} · ${caregiver.name}` : "No caregiver assigned"}</span>
        <button className="button button-subtle button-small" onClick={onStock}><History size={14} /> Stock history</button>
      </div>
    </article>
  );
}

function StockDialog({ medicine, caregivers, onClose, onSaved }) {
  const [transactions, setTransactions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [transactionType, setTransactionType] = useState("purchase");
  const [form, setForm] = useState({ quantity_change: "", recorded_by: "", notes: "" });

  useEffect(() => {
    api.stock(medicine.id)
      .then(setTransactions)
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, [medicine.id]);

  async function submit(event) {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    setSaving(true);
    setError("");
    try {
      await api.adjustStock(medicine.id, {
        quantity_change: form.quantity_change,
        transaction_type: transactionType,
        recorded_by: Number(form.recorded_by),
        notes: form.notes.trim() || null,
      });
      await onSaved();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={`${medicine.name} stock`} description={`Current balance: ${medicine.current_stock} units · Transactions are recorded for audit.`} onClose={onClose} wide>
      <div className="stock-dialog-grid">
        <form className="stock-adjust-form" onSubmit={submit}>
          <h3>Record an adjustment</h3>
          <Field label="Transaction type"><select value={transactionType} onChange={(event) => setTransactionType(event.target.value)}><option value="purchase">Purchase</option><option value="correction">Correction</option></select></Field>
          <Field label={transactionType === "purchase" ? "Units purchased" : "Adjustment (+/-)"}><input required type="number" step="0.001" min={transactionType === "purchase" ? "0.001" : undefined} value={form.quantity_change} onChange={(event) => setForm({ ...form, quantity_change: event.target.value })} placeholder={transactionType === "purchase" ? "e.g. 30" : "e.g. -2 or 2"} /></Field>
          <Field label="Recorded by"><select required value={form.recorded_by} onChange={(event) => setForm({ ...form, recorded_by: event.target.value })}><option value="">Select caregiver</option>{caregivers.map((person) => <option value={person.id} key={person.id}>{person.name}</option>)}</select></Field>
          <Field label="Note (optional)"><textarea rows="2" maxLength={2000} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></Field>
          <FormError>{error}</FormError>
          <button className="button button-primary button-full" disabled={saving}>{saving ? "Recording…" : <><PackagePlus size={16} /> Record transaction</>}</button>
        </form>
        <div className="transaction-history">
          <h3>Transaction history</h3>
          {loading && <LoadingState label="Loading transactions…" />}
          {!loading && error && <FormError>{error}</FormError>}
          {!loading && transactions && (transactions.transactions.length ? (
            <div className="transaction-list">
              {transactions.transactions.map((transaction) => (
                <div className="transaction-row" key={transaction.id}>
                  <span className={`transaction-icon transaction-${transaction.transaction_type}`}><ArrowUpRight size={16} /></span>
                  <span className="compact-copy"><strong>{transaction.transaction_type.replace("_", " ")}</strong><small>{transaction.notes || formatDateTime(transaction.created_at)}</small></span>
                  <strong className={Number(transaction.quantity_change) < 0 ? "amount-negative" : "amount-positive"}>{Number(transaction.quantity_change) > 0 ? "+" : ""}{transaction.quantity_change}</strong>
                </div>
              ))}
            </div>
          ) : <EmptyState icon={History} title="No transactions yet" description="Stock updates appear here after they are recorded." />)}
        </div>
      </div>
    </Modal>
  );
}
