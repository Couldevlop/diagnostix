import { Link } from "react-router-dom";

export function AdminDashboard() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line">
        <div className="container flex items-center justify-between py-5">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="font-serif text-[18px] font-medium tracking-tight text-ink">
              Nexus
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-clay">
              Diagnostix · Admin
            </span>
          </Link>
        </div>
      </header>
      <main className="container py-24">
        <span className="pill pill-clay mb-6">Tableau de bord</span>
        <h1 className="font-serif font-light text-[clamp(2rem,5vw,3.5rem)] leading-[1.05] tracking-tight">
          Dashboard.
        </h1>
        <p className="mt-4 text-[15px] text-ink-soft max-w-xl">
          KPIs agrégés, gestion des questions et paramètres, leads et journal
          d'audit — implémentation au Sprint 11 (cf. CLAUDE.md §14).
        </p>
      </main>
    </div>
  );
}
