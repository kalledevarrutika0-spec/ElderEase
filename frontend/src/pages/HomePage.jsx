import HealthStatus from "../components/HealthStatus.jsx";
import SiteHeader from "../components/SiteHeader.jsx";
import useHealthStatus from "../hooks/useHealthStatus.js";

export default function HomePage() {
  const health = useHealthStatus();

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 pb-16">
      <SiteHeader />
      <section className="grid min-h-[78vh] items-center gap-12 py-16 md:grid-cols-[1.15fr_0.85fr]">
        <div>
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">
            Intelligent family care coordination
          </p>
          <h1 className="max-w-2xl text-5xl font-semibold leading-[1.08] tracking-tight text-emerald-950 sm:text-6xl">
            Care works better when we do it together.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
            A calmer place for families to come together around the people they
            love. Your Elderease workspace is ready to grow.
          </p>
          <div className="mt-8">
            <HealthStatus status={health.status} error={health.error} />
          </div>
        </div>

        <aside className="rounded-3xl border border-emerald-950/10 bg-white p-8 shadow-[0_24px_70px_-48px_rgba(20,83,45,0.45)] sm:p-10">
          <div className="mb-8 grid h-14 w-14 place-items-center rounded-2xl bg-emerald-50 text-2xl text-emerald-800">
            ✳
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-emerald-950">
            A thoughtful start
          </h2>
          <p className="mt-3 leading-7 text-slate-600">
            The development environment is set up. This MVP foundation is
            designed to make room for the family care tools ahead.
          </p>
          <div className="mt-8 border-t border-slate-100 pt-5 text-sm text-slate-500">
            Frontend is running
          </div>
        </aside>
      </section>
    </main>
  );
}
