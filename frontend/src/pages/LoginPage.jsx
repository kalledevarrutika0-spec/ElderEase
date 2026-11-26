import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Activity, Eye, EyeOff, LogIn, UserPlus } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { Field, FormError } from "../components/UI.jsx";

export default function LoginPage() {
  const { session, loading, configured, signIn, signUp } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  if (!loading && session) return <Navigate to="/profile" replace />;

  async function submit(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      if (mode === "signup") {
        const data = await signUp(email, password);
        if (!data.session) {
          setNotice("Check your email to confirm your account, then sign in.");
        }
      } else {
        await signIn(email, password);
      }
    } catch (requestError) {
      setError(requestError.message || "Unable to complete authentication.");
    }
  }

  return (
    <main className="login-page">
      <section className="login-card" aria-labelledby="login-title">
        <div className="login-brand">
          <span className="brand-mark"><Activity size={21} /></span>
          <div><strong>Elderease</strong><small>Care, together</small></div>
        </div>
        <h1 id="login-title">{mode === "signup" ? "Create your account" : "Welcome back"}</h1>
        <p>Sign in to your secure family care space.</p>

        {!configured && (
          <FormError>Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.</FormError>
        )}

        <form onSubmit={submit}>
          <Field label="Email">
            <input type="email" required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" />
          </Field>
          <Field label="Password">
            <div className="password-row">
              <input type={showPassword ? "text" : "password"} required minLength={6} autoComplete={mode === "signup" ? "new-password" : "current-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 6 characters" />
              <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </Field>
          <FormError>{error}</FormError>
          {notice && <div className="success-banner">{notice}</div>}
          <button className="button button-primary login-submit" type="submit" disabled={!configured}>
            {mode === "signup" ? <UserPlus size={16} /> : <LogIn size={16} />}
            {mode === "signup" ? "Create account" : "Sign in"}
          </button>
        </form>

        <button className="login-mode-switch" type="button" onClick={() => { setMode((current) => current === "login" ? "signup" : "login"); setError(""); setNotice(""); }}>
          {mode === "login" ? "New to Elderease? Create an account" : "Already have an account? Sign in"}
        </button>
      </section>
    </main>
  );
}
