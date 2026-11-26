import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { HeartHandshake, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";
import { Field, FormError, LoadingState } from "../components/UI.jsx";

export default function ProfilePage() {
  const { session, loading: authLoading, logout } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [mode, setMode] = useState("create");
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    family_name: "",
    elder_name: "",
    elder_age: "",
    elder_care_notes: "",
    caregiver_name: "",
    relationship: "daughter",
    role: "Primary caregiver",
  });
  const [linkForm, setLinkForm] = useState({
    invite_code: "",
    caregiver_name: "",
    relationship: "daughter",
    role: "Caregiver",
  });

  useEffect(() => {
    if (!session) return;
    api.familyProfile()
      .then((data) => { setProfile(data); setForm({ ...form, family_name: data.family_name, elder_name: data.elder_name, elder_age: data.elder_age ?? "", elder_care_notes: data.elder_care_notes || "", caregiver_name: "", relationship: "daughter", role: "Primary caregiver" }); })
      .catch((requestError) => {
        if (!requestError.message?.includes("has not been created")) setError(requestError.message);
      })
      .finally(() => setLoading(false));
  }, [session]);

  if (!authLoading && !session) return <Navigate to="/login" replace />;

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submitCreate(event) {
    event.preventDefault();
    setError("");
    try {
      const data = await api.createFamilyProfile({
        ...form,
        elder_age: form.elder_age === "" ? null : Number(form.elder_age),
        elder_care_notes: form.elder_care_notes || null,
      });
      setProfile(data);
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function submitLinkSafe(event) {
    event.preventDefault();
    setError("");
    try {
      await api.linkFamilyMember({
        ...linkForm,
        invite_code: linkForm.invite_code.trim().toUpperCase(),
      });
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  if (authLoading || loading) return <LoadingState />;

  async function submitEdit(event) {
    event.preventDefault();
    setError("");
    try {
      await api.updateFamilyProfile({
        family_name: form.family_name,
        elder_name: form.elder_name,
        elder_age: form.elder_age === "" ? null : Number(form.elder_age),
        elder_care_notes: form.elder_care_notes || null,
      });
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  if (profile) {
    return (
      <main className="profile-page">
        <section className="profile-card">
          <div className="profile-heading">
            <span className="empty-icon"><HeartHandshake size={22} /></span>
            <div><p>FAMILY CARE PROFILE</p><h1>Edit family profile</h1></div>
          </div>
          <FormError>{error}</FormError>
          <form onSubmit={submitEdit}>
            <div className="profile-form-grid">
              <Field label="Family or care-circle name"><input required value={form.family_name} onChange={(event) => update("family_name", event.target.value)} /></Field>
              <Field label="Elder's name"><input required value={form.elder_name} onChange={(event) => update("elder_name", event.target.value)} /></Field>
              <Field label="Age (optional)"><input type="number" min="0" max="130" value={form.elder_age} onChange={(event) => update("elder_age", event.target.value)} /></Field>
              <Field label="Basic care information (optional)"><textarea value={form.elder_care_notes} onChange={(event) => update("elder_care_notes", event.target.value)} rows={3} /></Field>
            </div>
            <div className="profile-actions">
              <button className="button button-quiet" type="button" onClick={() => navigate("/", { replace: true })}>Cancel</button>
              <button className="button button-primary" type="submit"><ShieldCheck size={16} /> Save profile</button>
            </div>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="profile-page">
      <section className="profile-card">
        <div className="profile-heading">
          <span className="empty-icon"><HeartHandshake size={22} /></span>
          <div><p>FAMILY CARE PROFILE</p><h1>Set up your care circle</h1></div>
        </div>
        <div className="profile-tabs">
          <button className={mode === "create" ? "view-active" : ""} type="button" onClick={() => { setMode("create"); setError(""); }}>Create family</button>
          <button className={mode === "join" ? "view-active" : ""} type="button" onClick={() => { setMode("join"); setError(""); }}>Join with invite</button>
        </div>
        <FormError>{error}</FormError>

        {mode === "create" ? (
          <form onSubmit={submitCreate}>
            <div className="profile-form-grid">
              <Field label="Family or care-circle name"><input required value={form.family_name} onChange={(event) => update("family_name", event.target.value)} placeholder="The Sharma family" /></Field>
              <Field label="Elder's name"><input required value={form.elder_name} onChange={(event) => update("elder_name", event.target.value)} placeholder="Elder's name" /></Field>
              <Field label="Age (optional)"><input type="number" min="0" max="130" value={form.elder_age} onChange={(event) => update("elder_age", event.target.value)} /></Field>
              <Field label="Your name"><input required value={form.caregiver_name} onChange={(event) => update("caregiver_name", event.target.value)} placeholder="Your name" /></Field>
              <Field label="Relationship to elder"><input required value={form.relationship} onChange={(event) => update("relationship", event.target.value)} placeholder="daughter, son, spouse…" /></Field>
              <Field label="Role"><input required value={form.role} onChange={(event) => update("role", event.target.value)} /></Field>
              <Field label="Basic care information (optional)"><textarea value={form.elder_care_notes} onChange={(event) => update("elder_care_notes", event.target.value)} rows={3} placeholder="Only information needed for coordination" /></Field>
            </div>
            <div className="profile-actions">
              <button className="button button-quiet" type="button" onClick={logout}>Cancel</button>
              <button className="button button-primary" type="submit"><ShieldCheck size={16} /> Create family profile</button>
            </div>
          </form>
        ) : (
          <form onSubmit={submitLinkSafe}>
            <div className="profile-form-grid">
              <Field label="Invite code"><input required value={linkForm.invite_code} onChange={(event) => setLinkForm({ ...linkForm, invite_code: event.target.value })} placeholder="Enter family invite code" /></Field>
              <Field label="Your name"><input required value={linkForm.caregiver_name} onChange={(event) => setLinkForm({ ...linkForm, caregiver_name: event.target.value })} /></Field>
              <Field label="Relationship to elder"><input required value={linkForm.relationship} onChange={(event) => setLinkForm({ ...linkForm, relationship: event.target.value })} /></Field>
              <Field label="Role"><input required value={linkForm.role} onChange={(event) => setLinkForm({ ...linkForm, role: event.target.value })} /></Field>
            </div>
            <div className="profile-actions">
              <button className="button button-quiet" type="button" onClick={logout}>Cancel</button>
              <button className="button button-primary" type="submit"><HeartHandshake size={16} /> Join family</button>
            </div>
          </form>
        )}
      </section>
    </main>
  );
}
