import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export function AdminLogin() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line">
        <div className="container py-5">
          <Link to="/" className="btn-ghost text-[13px] -ml-3">
            <ArrowLeft size={16} />
            Retour
          </Link>
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <span className="pill pill-clay mb-6">Espace administrateur</span>
          <h1 className="font-serif font-light text-[40px] leading-[1.05] tracking-tight">
            Connexion.
          </h1>
          <p className="mt-3 text-[14px] text-ink-soft">
            Le formulaire d'authentification sera implémenté au Sprint 9.
          </p>

          <form className="mt-10 space-y-6 opacity-50 pointer-events-none">
            <div>
              <label className="block font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-2">
                Email
              </label>
              <input
                type="email"
                disabled
                placeholder="admin@openlabconsulting.com"
                className="w-full px-0 py-3 bg-transparent border-0 border-b border-line text-[15px] focus:outline-none focus:border-ink"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-2">
                Mot de passe
              </label>
              <input
                type="password"
                disabled
                placeholder="••••••••••••"
                className="w-full px-0 py-3 bg-transparent border-0 border-b border-line text-[15px] focus:outline-none focus:border-ink"
              />
            </div>
            <button type="button" disabled className="btn-clay w-full">
              Se connecter
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
