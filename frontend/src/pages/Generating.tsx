import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { api, ApiClientError } from "@/lib/api";

const STEPS = [
  "Calcul du score de maturité",
  "Évaluation des risques fiscaux & sociaux",
  "Modélisation prédictive (turnover, conformité)",
  "Analyse experte par notre IA",
  "Génération de votre rapport personnalisé",
];

export function Generating() {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const reportIdRef = useRef<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        const fin = await api.post<{ report_id: string; status: string }>(
          `/sessions/${sessionId}/finalize`
        );
        if (cancelled) return;
        reportIdRef.current = fin.report_id;
        setActiveStep(1);
        pollReport(fin.report_id);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiClientError
              ? err.detail
              : "La finalisation a échoué."
          );
        }
      }
    }

    function pollReport(reportId: string) {
      let stepTimer = 2;
      pollingRef.current = setInterval(async () => {
        try {
          const report = await api.get<{ status: string }>(
            `/reports/${reportId}`
          );
          if (cancelled) return;

          stepTimer++;
          setActiveStep(Math.min(4, Math.floor(stepTimer / 2)));

          if (report.status === "READY" || report.status === "FAILED") {
            clearInterval(pollingRef.current!);
            if (report.status === "READY") {
              navigate(`/diagnostic/report/${reportId}`);
            } else {
              setError("La génération du rapport a échoué. Veuillez réessayer.");
            }
          }
        } catch {
          // silent — retry on next tick
        }
      }, 2000);
    }

    start();

    return () => {
      cancelled = true;
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [sessionId, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
        <p className="font-serif text-[24px] text-ink mb-4">
          Une erreur est survenue
        </p>
        <p role="alert" className="text-[14px] text-ink-soft max-w-md">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-white">
      <motion.img
        src="/openlab.png"
        alt="OpenLab"
        className="h-12 w-auto mb-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      />
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="pill pill-clay mb-10"
      >
        Analyse en cours
      </motion.span>

      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.2 }}
        className="font-bold text-[clamp(1.75rem,4vw,2.75rem)]
                   leading-tight tracking-tight text-balance text-center max-w-xl text-ink"
      >
        Nous composons votre{" "}
        <span className="text-clay">rapport.</span>
      </motion.h1>

      <p className="mt-6 text-[14px] text-ink-soft text-center max-w-md">
        Cela prend une dizaine de secondes. Restez sur cette page.
      </p>

      <div className="mt-16 w-full max-w-md space-y-3">
        {STEPS.map((step, i) => (
          <Step
            key={step}
            label={step}
            state={
              i < activeStep ? "done" : i === activeStep ? "active" : "pending"
            }
          />
        ))}
      </div>
    </div>
  );
}

function Step({
  label,
  state,
}: {
  label: string;
  state: "pending" | "active" | "done";
}) {
  return (
    <div className="flex items-center gap-4">
      <span className="relative w-5 h-5 flex-shrink-0">
        <AnimatePresence mode="wait">
          {state === "pending" && (
            <motion.span
              key="pending"
              className="absolute inset-0 rounded-full border border-line"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
          )}
          {state === "active" && (
            <motion.span
              key="active"
              className="absolute inset-0 rounded-full border-2 border-clay"
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: [0.9, 1, 0.9] }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1.4, repeat: Infinity }}
            />
          )}
          {state === "done" && (
            <motion.span
              key="done"
              className="absolute inset-0 rounded-full bg-clay flex items-center justify-center"
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <svg
                viewBox="0 0 16 16"
                className="w-3 h-3 text-bone"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M3 8l3 3 7-7" />
              </svg>
            </motion.span>
          )}
        </AnimatePresence>
      </span>

      <span
        className={
          "text-[14px] transition-colors duration-300 " +
          (state === "done"
            ? "text-ink-soft line-through decoration-clay/40"
            : state === "active"
            ? "text-ink font-medium"
            : "text-ink-mute")
        }
      >
        {label}
      </span>
    </div>
  );
}
