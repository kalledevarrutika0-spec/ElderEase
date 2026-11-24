export default function SiteHeader() {
  return (
    <header className="flex items-center justify-between border-b border-emerald-950/10 py-5">
      <a
        className="flex items-center gap-2.5 font-semibold tracking-tight text-emerald-950"
        href="/"
        aria-label="Elderease home"
      >
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-800 text-lg text-white">
          e
        </span>
        Elderease
      </a>
      <span className="rounded-full bg-white px-3 py-1.5 text-xs font-medium text-emerald-900 ring-1 ring-emerald-900/10">
        MVP preview
      </span>
    </header>
  );
}
