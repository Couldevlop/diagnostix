import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";

export function AdminLogin() {
  const navigate = useNavigate();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const canSubmit = email.length > 0 && password.length > 0 && !submitting;

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.post<{ access_token: string; token_type: string; expires_in: number }>(
        "/auth/login", { email, password }
      );
      localStorage.setItem("nexus_admin_token", res.access_token);
      navigate("/admin");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.detail : "Identifiants incorrects.");
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Header */}
      <header className="border-b border-[#E5E5E5]">
        <div className="container py-3 flex items-center justify-between">
          <Link to="/" className="btn-ghost text-[13px] -ml-2 flex items-center gap-1.5">
            <ArrowLeft size={15} />
            <span className="hidden sm:inline">Retour à l'accueil</span>
            <span className="sm:hidden">Retour</span>
          </Link>
          <img src="/openlab.png" alt="OpenLab Consulting" className="h-11 sm:h-12 w-auto" />
        </div>
      </header>

      {/* Form */}
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-[380px] py-12">

          <div className="mb-8">
            <span className="pill text-[11px]">Espace administrateur</span>
            <h1 className="mt-5 font-black text-[36px] tracking-tight leading-none text-[#0A0A0A]">
              Connexion
            </h1>
            <p className="mt-2 text-[14px] text-[#888]">Accès réservé aux administrateurs OpenLab.</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5" noValidate>
            <div className="space-y-1.5">
              <label htmlFor="admin-email" className="block text-[12px] font-semibold text-[#3D3D3D] uppercase tracking-[0.08em]">
                Email
              </label>
              <input
                id="admin-email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@openlabconsulting.com"
                autoComplete="email"
                className="w-full px-4 py-3 rounded-lg border border-[#E5E5E5] bg-[#FAFAFA]
                           text-[15px] text-[#0A0A0A] placeholder:text-[#CCC]
                           focus:outline-none focus:border-[#FF5500] focus:bg-white
                           transition-all duration-150"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="admin-password" className="block text-[12px] font-semibold text-[#3D3D3D] uppercase tracking-[0.08em]">
                Mot de passe
              </label>
              <input
                id="admin-password"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••••••"
                autoComplete="current-password"
                className="w-full px-4 py-3 rounded-lg border border-[#E5E5E5] bg-[#FAFAFA]
                           text-[15px] text-[#0A0A0A] placeholder:text-[#CCC]
                           focus:outline-none focus:border-[#FF5500] focus:bg-white
                           transition-all duration-150"
              />
            </div>

            {error && (
              <p role="alert" className="text-[13px] font-medium text-red-600 bg-red-50 px-4 py-2.5 rounded-lg">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full flex items-center justify-center gap-2 py-3.5
                         rounded-full text-[15px] font-bold text-white
                         transition-all duration-200
                         disabled:opacity-30 disabled:cursor-not-allowed"
              style={{ background: canSubmit ? "#FF5500" : "#FF5500" }}
            >
              {submitting ? (
                <><Loader2 size={16} className="animate-spin" />Connexion…</>
              ) : "Se connecter"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
