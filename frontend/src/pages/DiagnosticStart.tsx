import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, ShieldCheck } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";

const COMPANY_SIZES = [
  { value: "1-10", label: "1 — 10" },
  { value: "11-50", label: "11 — 50" },
  { value: "51-200", label: "51 — 200" },
  { value: "201-500", label: "201 — 500" },
  { value: "500+", label: "500+" },
];

const SECTORS = [
  "Banque & Assurance",
  "BTP & Immobilier",
  "Commerce & Distribution",
  "Industrie & Manufacture",
  "Services & Conseil",
  "Technologie & Télécoms",
  "Transport & Logistique",
  "Agriculture & Agro-industrie",
  "Énergie & Mines",
  "Autre",
];

export function DiagnosticStart() {
  const navigate = useNavigate();
  const [companySize, setCompanySize] = useState<string>("");
  const [sector, setSector] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [consent, setConsent] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = companySize !== "" && sector !== "" && !submitting;

  async function handleStart() {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        company_size: companySize,
        sector,
        contact_consent: consent,
      };
      if (consent && email) {
        payload.contact_email = email;
      }
      const res = await api.post<{ session_id: string }>("/sessions", payload);
      navigate(`/diagnostic/${res.session_id}/q/1`);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.detail
          : "Une erreur est survenue. Réessayez."
      );
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line bg-white sticky top-0 z-30">
        <div className="container flex items-center justify-between h-[72px]">
          <Link to="/" className="btn-ghost text-[13px] -ml-2 flex items-center gap-1.5">
            <ArrowLeft size={15} />
            <span className="hidden sm:inline">Accueil</span>
          </Link>
          <img src="/openlab.png" alt="OpenLab" className="h-11 sm:h-12 w-auto" />
          <div className="w-16 sm:w-20" />
        </div>
      </header>

      <main className="container flex-1 py-16 lg:py-24 grid grid-cols-12 gap-8 lg:gap-16">
        <motion.aside
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="col-span-12 md:col-span-5 lg:col-span-5"
        >
          <span className="pill pill-clay mb-8">Avant de commencer</span>
          <h1 className="font-serif font-light leading-[1] tracking-tight
                         text-[clamp(2.25rem,4.5vw,3.5rem)] text-balance">
            Quelques <em className="text-clay font-extralight">repères</em> pour
            personnaliser votre diagnostic.
          </h1>
          <p className="mt-8 text-[15px] leading-relaxed text-ink-soft max-w-md">
            Aucune information nominative n'est requise. L'email est optionnel
            et ne sert qu'à recevoir votre rapport. Vous restez en contrôle.
          </p>

          <hr className="rule-clay mt-12" />
          <div className="mt-6 space-y-3 text-[13px] text-ink-soft">
            <Detail label="Durée estimée" value="≈ 5 minutes" />
            <Detail label="Questions" value="20" />
            <Detail label="Format de rendu" value="Rapport PDF · 12 pages" />
          </div>
        </motion.aside>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="col-span-12 md:col-span-7 lg:col-start-7 lg:col-span-6 space-y-12"
        >
          <Field
            number="01"
            label="Quelle est la taille de votre entreprise ?"
            sublabel="Effectif total, tous statuts confondus."
          >
            <div className="flex flex-wrap gap-2">
              {COMPANY_SIZES.map((size) => (
                <SizeChip
                  key={size.value}
                  selected={companySize === size.value}
                  onClick={() => setCompanySize(size.value)}
                >
                  {size.label}
                </SizeChip>
              ))}
            </div>
          </Field>

          <Field
            number="02"
            label="Dans quel secteur d'activité ?"
            sublabel="Pour calibrer les benchmarks sectoriels."
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SECTORS.map((s) => (
                <SectorChip
                  key={s}
                  selected={sector === s}
                  onClick={() => setSector(s)}
                >
                  {s}
                </SectorChip>
              ))}
            </div>
          </Field>

          <Field
            number="03"
            label="Recevoir le rapport par email ?"
            sublabel="Optionnel. Vous pourrez aussi le télécharger directement."
          >
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="prenom.nom@entreprise.ci"
              className="w-full px-0 py-3 bg-transparent
                         border-0 border-b border-line
                         text-[16px] text-ink placeholder:text-ink-mute
                         focus:outline-none focus:border-ink
                         transition-colors duration-200"
              autoComplete="email"
            />

            <label className="mt-6 flex items-start gap-3 cursor-pointer group select-none">
              <span className="relative flex-shrink-0 mt-0.5">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="peer sr-only"
                />
                <span
                  className="block w-[18px] h-[18px] border border-line bg-bone-card
                             transition-all duration-200
                             peer-checked:bg-ink peer-checked:border-ink
                             group-hover:border-ink"
                />
                <svg
                  viewBox="0 0 16 16"
                  className="absolute inset-0 m-auto w-3 h-3 text-bone
                             opacity-0 peer-checked:opacity-100 transition-opacity"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ pointerEvents: "none" }}
                >
                  <path d="M3 8l3 3 7-7" />
                </svg>
              </span>
              <span className="text-[13px] leading-relaxed text-ink-soft
                                group-hover:text-ink transition-colors">
                J'accepte que mon email soit conservé chiffré uniquement pour
                m'envoyer le rapport. Aucune réutilisation commerciale.
              </span>
            </label>
          </Field>

          {error && (
            <p role="alert" className="text-[13px] text-red-600 -mt-6">
              {error}
            </p>
          )}

          <div className="pt-4 border-t border-line">
            <div className="flex items-center justify-between gap-6 flex-wrap">
              <button
                type="button"
                disabled={!canSubmit}
                onClick={handleStart}
                className="btn-clay disabled:opacity-30 disabled:cursor-not-allowed"
              >
                {submitting ? "Démarrage…" : "Lancer le diagnostic"}
                <ArrowRight size={18} />
              </button>

              <span className="flex items-center gap-2 text-[12px] text-ink-mute">
                <ShieldCheck size={14} className="text-clay" />
                Conforme ARTCI · Loi 2013-450
              </span>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-baseline gap-4">
      <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute">
        {label}
      </span>
      <span className="text-[14px] text-ink">{value}</span>
    </div>
  );
}

function Field({
  number,
  label,
  sublabel,
  children,
}: {
  number: string;
  label: string;
  sublabel?: string;
  children: React.ReactNode;
}) {
  return (
    <fieldset className="space-y-5">
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-[11px] tracking-[0.2em] text-clay">
          {number}
        </span>
        <legend className="font-serif text-[20px] font-normal text-ink">
          {label}
        </legend>
      </div>
      {sublabel && (
        <p className="text-[13px] text-ink-mute -mt-3">{sublabel}</p>
      )}
      <div>{children}</div>
    </fieldset>
  );
}

function SizeChip({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-selected={selected}
      className="px-5 py-2.5 text-[14px] font-medium tabular border rounded-full
                 transition-all duration-200
                 data-[selected=false]:border-line data-[selected=false]:bg-bone-card
                 data-[selected=false]:text-ink-soft
                 data-[selected=true]:bg-ink data-[selected=true]:border-ink
                 data-[selected=true]:text-bone"
    >
      {children}
    </button>
  );
}

function SectorChip({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-selected={selected}
      className="text-left px-4 py-3 text-[14px] border rounded transition-all duration-200
                 data-[selected=false]:border-line data-[selected=false]:bg-bone-card
                 data-[selected=false]:text-ink-soft
                 data-[selected=true]:bg-ink data-[selected=true]:border-ink
                 data-[selected=true]:text-bone"
    >
      {children}
    </button>
  );
}
