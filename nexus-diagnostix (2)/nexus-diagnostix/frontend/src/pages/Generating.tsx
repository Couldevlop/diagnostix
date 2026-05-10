import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

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

  useEffect(() => {
    // Animation de progression — le vrai polling sera branché au Sprint 7
    const tick = window.setInterval(() => {
      setActiveStep((s) => {
        if (s >= STEPS.length - 1) {
          window.clearInterval(tick);
          window.setTimeout(
            () => navigate(`/diagnostic/report/preview-${sessionId}`),
            900
          );
          return s;
        }
        return s + 1;
      });
    }, 1100);
    return () => window.clearInterval(tick);
  }, [navigate, sessionId]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="pill pill-clay mb-12"
      >
        Analyse en cours
      </motion.span>

      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.1 }}
        className="font-serif font-light text-[clamp(2rem,5vw,3.5rem)]
                   leading-[1.05] tracking-tight text-balance text-center max-w-2xl"
      >
        Nous composons votre{" "}
        <em className="text-clay font-extralight">rapport.</em>
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
              animate={{
                opacity: 1,
                scale: [0.9, 1, 0.9],
              }}
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
