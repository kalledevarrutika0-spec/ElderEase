import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { Activity, ChevronDown, Eye, EyeOff, LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { Field, FormError } from "../components/UI.jsx";

const QUOTES = [
  "Family is where care begins, and where it never ends.",
  "The little moments together become the memories we hold forever.",
  "Looking after the ones who raised us is love coming full circle.",
  "Every dose remembered and every visit planned says “I’m here.”",
];

function scrollToSignIn() {
  document.getElementById("signin")?.scrollIntoView({ behavior: "smooth" });
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [quoteIndex, setQuoteIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setQuoteIndex((index) => (index + 1) % QUOTES.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  if (user) return <Navigate to="/" replace />;

  function submit(event) {
    event.preventDefault();
    setError("");
    try {
      login(email, password);
    } catch (loginError) {
      setError(loginError.message);
    }
  }

  return (
    <div className="login-page">
      <section className="login-hero">
        <div className="hero-brand">
          <span className="brand-mark"><Activity size={21} /></span>
          <div>
            <strong>Elderease</strong>
            <small>Care, together</small>
          </div>
        </div>

        <div className="hero-center">
          <blockquote className="hero-quote" key={quoteIndex}>
            {QUOTES[quoteIndex]}
          </blockquote>
          <div className="hero-dots" aria-hidden="true">
            {QUOTES.map((_, index) => (
              <i key={index} className={index === quoteIndex ? "dot-active" : ""} />
            ))}
          </div>
        </div>

        <button className="hero-scroll" onClick={scrollToSignIn} aria-label="Scroll to sign in">
          <span>Sign in</span>
          <ChevronDown size={22} />
        </button>
      </section>

      <section className="login-section" id="signin">
        <form className="login-card" onSubmit={submit}>
          <div className="login-brand">
            <span className="brand-mark"><Activity size={21} /></span>
            <div>
              <strong>Elderease</strong>
              <small>Care, together</small>
            </div>
          </div>
          <h1>Welcome back</h1>
          <p className="login-sub">Sign in to your family care space.</p>

          <Field label="Email">
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          </Field>

          <Field label="Password">
            <div className="password-row">
              <input
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </Field>

          <FormError>{error}</FormError>

          <button className="button button-primary login-submit" type="submit">
            <LogIn size={16} /> Sign in
          </button>

          <div className="login-demo">
            Demo login: <strong>family@elderease.com</strong> / <strong>care1234</strong>
          </div>
        </form>
      </section>
    </div>
  );
}