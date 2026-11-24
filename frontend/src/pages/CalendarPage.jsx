import { useMemo, useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock3,
  MapPin,
  Pencil,
  Plus,
  RefreshCw,
  Trash2,
  UserRound,
} from "lucide-react";
import { api } from "../services/api.js";
import useLoadData from "../hooks/useLoadData.js";
import { formatDateTime, localDateTimeValue } from "../utils/format.js";
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
const emptyForm = {
  title: "",
  doctor_name: "",
  location: "",
  appointment_datetime: "",
  assigned_caregiver_id: "",
  status: "scheduled",
  notes: "",
};

function loadCalendar() {
  return Promise.all([api.appointments(), api.caregivers()]).then(([appointments, caregivers]) => ({
    appointments: itemsOf(appointments),
    caregivers: itemsOf(caregivers),
  }));
}

export default function CalendarPage() {
  const { data, loading, error, refresh } = useLoadData(loadCalendar, []);
  const [view, setView] = useState("list");
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [dialog, setDialog] = useState(null);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const appointments = data?.appointments || [];
  const caregivers = data?.caregivers || [];
  const caregiverById = new Map(caregivers.map((person) => [person.id, person]));
  const sortedAppointments = [...appointments].sort((a, b) => new Date(a.appointment_datetime) - new Date(b.appointment_datetime));

  function openForm(appointment = null) {
    setFormError("");
    setDialog({
      appointment,
      form: appointment
        ? {
            title: appointment.title,
            doctor_name: appointment.doctor_name,
            location: appointment.location || "",
            appointment_datetime: localDateTimeValue(appointment.appointment_datetime),
            assigned_caregiver_id: appointment.assigned_caregiver_id ? String(appointment.assigned_caregiver_id) : "",
            status: appointment.status,
            notes: appointment.notes || "",
          }
        : { ...emptyForm, appointment_datetime: localDateTimeValue() },
    });
  }

  async function saveAppointment(event) {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    setSaving(true);
    setFormError("");
    const form = dialog.form;
    const payload = {
      title: form.title.trim(),
      doctor_name: form.doctor_name.trim(),
      location: form.location.trim() || null,
      appointment_datetime: new Date(form.appointment_datetime).toISOString(),
      assigned_caregiver_id: form.assigned_caregiver_id ? Number(form.assigned_caregiver_id) : null,
      status: form.status,
      notes: form.notes.trim() || null,
    };
    try {
      if (dialog.appointment) await api.updateAppointment(dialog.appointment.id, payload);
      else await api.createAppointment(payload);
      setDialog(null);
      setNotice(dialog.appointment ? "Appointment updated." : "Appointment added to the family calendar.");
      await refresh();
    } catch (requestError) {
      setFormError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function deleteAppointment(appointment) {
    if (!window.confirm(`Remove "${appointment.title}" from the calendar?`)) return;
    setFormError("");
    try {
      await api.deleteAppointment(appointment.id);
      setNotice("Appointment removed.");
      await refresh();
    } catch (requestError) {
      setFormError(requestError.message);
    }
  }

  const calendarDays = useMemo(() => makeCalendarDays(month), [month]);
  const appointmentsByDate = new Map();
  appointments.forEach((appointment) => {
    const key = localDateKey(new Date(appointment.appointment_datetime));
    appointmentsByDate.set(key, [...(appointmentsByDate.get(key) || []), appointment]);
  });

  return (
    <>
      <PageHeader
        eyebrow="FAMILY SCHEDULE"
        title="Care calendar"
        description="Keep appointments and caregiver plans easy to find and share."
        actions={<button className="button button-primary" onClick={() => openForm()}><Plus size={16} /> Add appointment</button>}
      />
      {notice && <div className="success-banner">{notice}<button onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}
      {formError && !dialog && <div className="inline-error" role="alert">{formError}</div>}
      {loading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refresh} />}
      {data && (
        <section className="surface-card calendar-surface">
          <div className="calendar-toolbar">
            <div className="view-switch" role="group" aria-label="Calendar display">
              <button className={view === "list" ? "view-active" : ""} onClick={() => setView("list")}><Clock3 size={15} /> List</button>
              <button className={view === "month" ? "view-active" : ""} onClick={() => setView("month")}><CalendarDays size={15} /> Month</button>
            </div>
            {view === "month" && (
              <div className="month-picker">
                <button className="icon-button" aria-label="Previous month" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() - 1, 1))}><ChevronLeft size={18} /></button>
                <strong>{month.toLocaleDateString(undefined, { month: "long", year: "numeric" })}</strong>
                <button className="icon-button" aria-label="Next month" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() + 1, 1))}><ChevronRight size={18} /></button>
                <button className="button button-quiet" onClick={() => setMonth(new Date(new Date().getFullYear(), new Date().getMonth(), 1))}>Today</button>
              </div>
            )}
            <button className="icon-button" aria-label="Refresh appointments" onClick={refresh}><RefreshCw size={16} /></button>
          </div>
          {view === "list" ? (
            sortedAppointments.length ? (
              <div className="appointment-list">
                {sortedAppointments.map((appointment) => {
                  const caregiver = caregiverById.get(appointment.assigned_caregiver_id);
                  return (
                    <article className="appointment-row" key={appointment.id}>
                      <div className="appointment-date-block">
                        <strong>{new Date(appointment.appointment_datetime).getDate()}</strong>
                        <span>{new Date(appointment.appointment_datetime).toLocaleDateString(undefined, { month: "short" })}</span>
                      </div>
                      <div className="appointment-info">
                        <div className="appointment-title-line"><h2>{appointment.title}</h2><StatusPill tone={appointment.status === "cancelled" ? "muted" : appointment.status === "completed" ? "success" : "neutral"}>{appointment.status}</StatusPill></div>
                        <p>{appointment.doctor_name}</p>
                        <div className="appointment-meta">
                          <span><Clock3 size={14} />{formatDateTime(appointment.appointment_datetime)}</span>
                          {appointment.location && <span><MapPin size={14} />{appointment.location}</span>}
                          <span><UserRound size={14} />{caregiver?.name || "Caregiver unassigned"}</span>
                        </div>
                        {appointment.notes && <p className="appointment-notes">{appointment.notes}</p>}
                      </div>
                      <div className="appointment-actions">
                        <button className="icon-button" onClick={() => openForm(appointment)} aria-label={`Edit ${appointment.title}`}><Pencil size={16} /></button>
                        <button className="icon-button icon-danger-button" onClick={() => deleteAppointment(appointment)} aria-label={`Delete ${appointment.title}`}><Trash2 size={16} /></button>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : <EmptyState icon={CalendarDays} title="Your calendar is open" description="Add an appointment and assign a caregiver to keep the family in sync." action={<button className="button button-primary" onClick={() => openForm()}><Plus size={16} /> Add appointment</button>} />
          ) : (
            <div className="month-calendar">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => <div className="calendar-weekday" key={day}>{day}</div>)}
              {calendarDays.map((date, index) => {
                if (!date) return <div className="calendar-day calendar-day-empty" key={`empty-${index}`} />;
                const key = localDateKey(date);
                const dayEvents = appointmentsByDate.get(key) || [];
                const isToday = date.toDateString() === new Date().toDateString();
                return (
                  <div className={`calendar-day${isToday ? " calendar-today" : ""}`} key={key}>
                    <span className="calendar-day-number">{date.getDate()}</span>
                    {dayEvents.slice(0, 2).map((appointment) => (
                      <button className="calendar-event" key={appointment.id} onClick={() => openForm(appointment)} title={`${appointment.title} · ${appointment.doctor_name}`}>
                        <span>{appointment.title}</span><small>{dateTimeLabel(appointment.appointment_datetime)}</small>
                      </button>
                    ))}
                    {dayEvents.length > 2 && <small className="calendar-more">+{dayEvents.length - 2} more</small>}
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}
      {data && <div className="calendar-footnote"><CalendarDays size={15} />Appointments are displayed in your local time zone. {appointments.length} total in the family calendar.</div>}
      {dialog && (
        <Modal title={dialog.appointment ? "Edit appointment" : "Add an appointment"} description="Add visit details and choose who is coordinating the appointment." onClose={() => setDialog(null)}>
          <form className="form-stack" onSubmit={saveAppointment}>
            <Field label="Appointment title"><input required maxLength={160} value={dialog.form.title} onChange={(event) => updateAppointmentForm(setDialog, event.target.name, event.target.value)} name="title" placeholder="e.g. Annual check-up" /></Field>
            <Field label="Doctor or provider"><input required maxLength={120} value={dialog.form.doctor_name} onChange={(event) => updateAppointmentForm(setDialog, event.target.name, event.target.value)} name="doctor_name" placeholder="Provider name" /></Field>
            <Field label="Date and time"><input required type="datetime-local" value={dialog.form.appointment_datetime} onChange={(event) => updateAppointmentForm(setDialog, event.target.name, event.target.value)} name="appointment_datetime" /></Field>
            <Field label="Location"><input maxLength={240} value={dialog.form.location} onChange={(event) => updateAppointmentForm(setDialog, event.target.name, event.target.value)} name="location" placeholder="Clinic or address" /></Field>
            <Field label="Caregiver"><select value={dialog.form.assigned_caregiver_id} onChange={(event) => updateAppointmentForm(setDialog, event.target.name, event.target.value)} name="assigned_caregiver_id"><option value="">Unassigned</option>{caregivers.map((caregiver) => <option value={caregiver.id} key={caregiver.id}>{caregiver.name} · {caregiver.relationship}</option>)}</select></Field>
            <Field label="Status"><select value={dialog.form.status} onChange={(event) => updateAppointmentForm(setDialog, event.target.name, event.target.value)} name="status"><option value="scheduled">Scheduled</option><option value="confirmed">Confirmed</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option></select></Field>
            <Field label="Notes"><textarea rows="3" maxLength={4000} value={dialog.form.notes} onChange={(event) => updateAppointmentForm(setDialog, event.target.name, event.target.value)} name="notes" placeholder="Optional details for the family" /></Field>
            <FormError>{formError}</FormError>
            <div className="form-footer"><button type="button" className="button button-quiet" onClick={() => setDialog(null)}>Cancel</button><button className="button button-primary" disabled={saving}>{saving ? "Saving…" : dialog.appointment ? "Save changes" : "Add appointment"}</button></div>
          </form>
        </Modal>
      )}
    </>
  );
}

function updateAppointmentForm(setDialog, name, value) {
  setDialog((current) => ({ ...current, form: { ...current.form, [name]: value } }));
}

function makeCalendarDays(month) {
  const firstDay = new Date(month.getFullYear(), month.getMonth(), 1).getDay();
  const count = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  return [...Array(firstDay).fill(null), ...Array.from({ length: count }, (_, day) => new Date(month.getFullYear(), month.getMonth(), day + 1))];
}

function dateTimeLabel(value) {
  return new Date(value).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function localDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
