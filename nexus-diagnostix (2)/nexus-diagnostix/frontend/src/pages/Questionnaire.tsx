import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight, ChevronDown } from "lucide-react";

/* -------------------------------------------------------------------------- */
/*  Données d'essai                                                           */
/*  Ces 20 questions seront remplacées par un GET /sessions/:id/questions     */
/*  au Sprint 6. La forme exacte du JSON est respectée pour minimiser le      */
/*  travail d'intégration ultérieur.                                          */
/* -------------------------------------------------------------------------- */

interface Question {
  id: number;
  code: string;
  label: string;
  category: "FISCALE" | "SOCIALE" | "CONFORMITE" | "DIGITALE";
  answer_type:
    | "YES_NO"
    | "YES_NO_PARTIAL"
    | "YES_NO_MANUAL"
    | "FREE_NUMERIC";
  help_text: string | null;
}

const QUESTIONS: Question[] = [
  { id: 1,  code: "Q01", category: "FISCALE",   answer_type: "YES_NO_PARTIAL", label: "Vos bulletins de paie intègrent-ils la réforme IGR 2024 ?", help_text: "La réforme fiscale 2024 a modifié le barème de l'IGR. Vérifiez que votre logiciel a été mis à jour." },
  { id: 2,  code: "Q02", category: "SOCIALE",   answer_type: "YES_NO_MANUAL",  label: "Le calcul de vos IFC est-il automatisé selon la Convention Collective ?", help_text: "L'IFC suit des taux progressifs : 30 % de 1 à 5 ans, 35 % de 6 à 10 ans, 40 % au-delà." },
  { id: 3,  code: "Q03", category: "SOCIALE",   answer_type: "YES_NO",         label: "Le système bloque-t-il les dépassements d'heures supplémentaires au-delà du plafond légal ?", help_text: "Plafond hebdomadaire : 15 h. Plafond annuel : 75 h." },
  { id: 4,  code: "Q04", category: "CONFORMITE", answer_type: "YES_NO",        label: "Disposez-vous d'un historique d'audit modifiable uniquement par l'administrateur ?", help_text: "Un journal d'audit immuable est exigé pour la traçabilité réglementaire." },
  { id: 5,  code: "Q05", category: "DIGITALE",  answer_type: "YES_NO_PARTIAL", label: "Vos DISA sont-elles générées automatiquement sans retraitement Excel ?", help_text: "La DISA est obligatoire auprès de la CNPS." },
  { id: 6,  code: "Q06", category: "DIGITALE",  answer_type: "YES_NO",         label: "Délai moyen de sortie de paie : moins de 2 jours après la fin du mois ?", help_text: null },
  { id: 7,  code: "Q07", category: "DIGITALE",  answer_type: "YES_NO",         label: "Vos processus de validation de congés sont-ils 100 % sans papier ?", help_text: null },
  { id: 8,  code: "Q08", category: "DIGITALE",  answer_type: "FREE_NUMERIC",   label: "Temps hebdomadaire perdu en saisie de données RH (en heures) ?", help_text: "Estimez le total hebdomadaire pour l'équipe RH (saisie, ressaisie, copier-coller)." },
  { id: 9,  code: "Q09", category: "DIGITALE",  answer_type: "YES_NO",         label: "Les employés reçoivent-ils leurs bulletins sur un portail sécurisé ?", help_text: null },
  { id: 10, code: "Q10", category: "SOCIALE",   answer_type: "YES_NO",         label: "Les prêts et avances sont-ils déduits automatiquement en paie ?", help_text: null },
  { id: 11, code: "Q11", category: "DIGITALE",  answer_type: "YES_NO",         label: "Générez-vous votre bilan social en un seul clic ?", help_text: "Le bilan social annuel est obligatoire pour les entreprises de plus de 300 salariés." },
  { id: 12, code: "Q12", category: "DIGITALE",  answer_type: "YES_NO",         label: "Recevez-vous des alertes 30 jours avant la fin d'un CDD ou d'une période d'essai ?", help_text: null },
  { id: 13, code: "Q13", category: "DIGITALE",  answer_type: "YES_NO",         label: "Avez-vous une cartographie digitale des compétences critiques ?", help_text: null },
  { id: 14, code: "Q14", category: "DIGITALE",  answer_type: "YES_NO",         label: "Vos entretiens annuels sont-ils liés numériquement aux objectifs ?", help_text: null },
  { id: 15, code: "Q15", category: "DIGITALE",  answer_type: "YES_NO",         label: "Suivez-vous l'absentéisme en temps réel par département ?", help_text: null },
  { id: 16, code: "Q16", category: "DIGITALE",  answer_type: "YES_NO",         label: "Votre système peut-il prédire les risques de turnover ?", help_text: "Les outils modernes utilisent le machine learning pour anticiper les départs à 12 mois." },
  { id: 17, code: "Q17", category: "DIGITALE",  answer_type: "YES_NO",         label: "Avez-vous un Assistant IA pour les questions RH récurrentes ?", help_text: null },
  { id: 18, code: "Q18", category: "DIGITALE",  answer_type: "YES_NO",         label: "Simulez-vous l'impact d'une hausse de masse salariale en 10 secondes ?", help_text: null },
  { id: 19, code: "Q19", category: "DIGITALE",  answer_type: "YES_NO",         label: "Gérez-vous plusieurs sites ou pays sur une interface unique ?", help_text: null },
  { id: 20, code: "Q20", category: "CONFORMITE", answer_type: "YES_NO",        label: "Votre base de données est-elle déclarée conforme à la loi ARTCI ?", help_text: "La Loi 2013-450 impose une déclaration auprès de l'ARTCI." },
];

const CATEGORY_LABELS: Record<Question["category"], string> = {
  FISCALE: "Fiscalité",
  SOCIALE: "Conformité sociale",
  CONFORMITE: "Gouvernance",
  DIGITALE: "Maturité digitale",
};

interface AnswerOption {
  value: string;
  label: string;
  helper?: string;
  shortcut: string;
}

function getOptions(type: Question["answer_type"]): AnswerOption[] {
  switch (type) {
    case "YES_NO":
      return [
        { value: "YES", label: "Oui", shortcut: "1" },
        { value: "NO",  label: "Non", shortcut: "2" },
      ];
    case "YES_NO_PARTIAL":
      return [
        { value: "YES",     label: "Oui",                    shortcut: "1", helper: "Pleinement en place" },
        { value: "PARTIAL", label: "Partiellement",          shortcut: "2", helper: "Mise en place en cours" },
        { value: "NO",      label: "Non",                    shortcut: "3", helper: "Pas encore" },
      ];
    case "YES_NO_MANUAL":
      return [
        { value: "YES",    label: "Oui, automatisé", shortcut: "1" },
        { value: "MANUAL", label: "Calculé manuellement", shortcut: "2", helper: "Excel, papier ou calcul à la main" },
        { value: "NO",     label: "Non géré", shortcut: "3" },
      ];
    case "FREE_NUMERIC":
      return [];
  }
}

/* -------------------------------------------------------------------------- */
/*  Composant principal                                                       */
/* -------------------------------------------------------------------------- */

export function Questionnaire() {
  const navigate = useNavigate();
  const { sessionId, questionIndex } = useParams();
  const idx = Math.max(1, Math.min(20, parseInt(questionIndex ?? "1", 10)));
  const question = QUESTIONS[idx - 1]!;

  // État des réponses (clé = id de question)
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [numericValue, setNumericValue] = useState<string>("");
  const [direction, setDirection] = useState<1 | -1>(1);

  const currentAnswer = answers[question.id] ?? "";
  const options = useMemo(() => getOptions(question.answer_type), [question.answer_type]);
  const isNumeric = question.answer_type === "FREE_NUMERIC";

  const canGoNext = isNumeric
    ? numericValue !== "" && !isNaN(Number(numericValue))
    : currentAnswer !== "";

  // Synchronise le champ numérique quand on revient sur la question
  useEffect(() => {
    if (isNumeric) {
      setNumericValue(answers[question.id] ?? "");
    }
  }, [question.id, isNumeric, answers]);

  function selectAnswer(value: string) {
    setAnswers((prev) => ({ ...prev, [question.id]: value }));
    // Auto-avance après 250ms (UX Typeform)
    window.setTimeout(() => goNext(value), 250);
  }

  function commitNumeric() {
    if (!canGoNext) return;
    setAnswers((prev) => ({ ...prev, [question.id]: numericValue }));
    goNext(numericValue);
  }

  function goNext(_value?: string) {
    setDirection(1);
    if (idx >= 20) {
      navigate(`/diagnostic/${sessionId}/generating`);
    } else {
      navigate(`/diagnostic/${sessionId}/q/${idx + 1}`);
    }
  }

  function goPrev() {
    if (idx <= 1) return;
    setDirection(-1);
    navigate(`/diagnostic/${sessionId}/q/${idx - 1}`);
  }

  // Raccourcis clavier (1, 2, 3 + Entrée)
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (isNumeric) {
        if (e.key === "Enter" && canGoNext) commitNumeric();
        return;
      }
      const opt = options.find((o) => o.shortcut === e.key);
      if (opt) {
        e.preventDefault();
        selectAnswer(opt.value);
      } else if (e.key === "Enter" && canGoNext) {
        goNext();
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, isNumeric, canGoNext, options, numericValue]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar fine */}
      <header className="border-b border-line">
        <div className="container flex items-center justify-between py-4">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="font-serif text-[16px] font-medium tracking-tight text-ink">
              Nexus
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-clay">
              Diagnostix
            </span>
          </Link>

          <div className="flex items-center gap-6">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute">
              {CATEGORY_LABELS[question.category]}
            </span>
            <span className="tabular text-[12px] text-ink-soft">
              <span className="text-ink font-medium">{idx}</span>
              <span className="text-ink-mute mx-1">/</span>
              <span className="text-ink-mute">20</span>
            </span>
          </div>
        </div>
        {/* Progress hairline */}
        <div className="progress-track">
          <motion.div
            className="progress-fill"
            initial={false}
            animate={{ width: `${(idx / 20) * 100}%` }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
      </header>

      <main className="flex-1 container py-12 lg:py-20 grid grid-cols-12 gap-8 lg:gap-16">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={idx}
            custom={direction}
            initial={{ opacity: 0, x: direction * 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -direction * 24 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="col-span-12 grid grid-cols-12 gap-8 lg:gap-16"
          >
            {/* Numéro géant à gauche, signature éditoriale */}
            <div className="hidden md:block md:col-span-3 lg:col-span-3">
              <div className="sticky top-32">
                <div className="question-number text-[clamp(8rem,18vw,16rem)]">
                  {String(idx).padStart(2, "0")}
                </div>
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mt-2 ml-2">
                  {question.code}
                </div>
              </div>
            </div>

            {/* Contenu de la question */}
            <div className="col-span-12 md:col-span-9 lg:col-start-5 lg:col-span-8">
              {/* Numéro mobile */}
              <div className="md:hidden mb-6">
                <span className="font-mono text-[11px] tracking-[0.2em] text-clay">
                  Question {idx} · {String(idx).padStart(2, "0")} / 20
                </span>
              </div>

              {/* Énoncé */}
              <h2 className="font-serif font-light leading-[1.15] tracking-tight
                             text-[clamp(1.625rem,3vw,2.5rem)] text-ink text-balance">
                {question.label}
              </h2>

              {question.help_text && (
                <details className="mt-6 group">
                  <summary className="inline-flex items-center gap-1.5 text-[12px]
                                       text-ink-mute hover:text-ink cursor-pointer
                                       transition-colors list-none">
                    <ChevronDown
                      size={14}
                      className="transition-transform duration-200 group-open:rotate-180"
                    />
                    Comprendre cette question
                  </summary>
                  <p className="mt-3 text-[13px] leading-relaxed text-ink-soft pl-5
                                border-l border-line py-1">
                    {question.help_text}
                  </p>
                </details>
              )}

              {/* Réponses */}
              <div className="mt-12 space-y-3 max-w-2xl">
                {isNumeric ? (
                  <NumericInput
                    value={numericValue}
                    onChange={setNumericValue}
                    onSubmit={commitNumeric}
                  />
                ) : (
                  options.map((opt, i) => (
                    <motion.button
                      key={opt.value}
                      type="button"
                      data-selected={currentAnswer === opt.value}
                      onClick={() => selectAnswer(opt.value)}
                      className="answer-card group"
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: 0.15 + i * 0.06 }}
                    >
                      <span className="answer-key">{opt.shortcut}</span>
                      <span className="flex-1">
                        <span className="block text-[16px] font-medium tracking-tight">
                          {opt.label}
                        </span>
                        {opt.helper && (
                          <span className="block mt-0.5 text-[12px] opacity-60">
                            {opt.helper}
                          </span>
                        )}
                      </span>
                    </motion.button>
                  ))
                )}
              </div>

              {/* Hint clavier */}
              <p className="mt-8 text-[11px] text-ink-mute">
                {isNumeric ? (
                  <>
                    Appuyez sur <Kbd>Entrée</Kbd> pour valider
                  </>
                ) : (
                  <>
                    Tapez <Kbd>1</Kbd>
                    {options.length > 1 && <> ou <Kbd>2</Kbd></>}
                    {options.length > 2 && <> ou <Kbd>3</Kbd></>}{" "}
                    pour répondre
                  </>
                )}
              </p>
            </div>
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Footer navigation */}
      <footer className="border-t border-line bg-bone-card">
        <div className="container flex items-center justify-between py-4">
          <button
            type="button"
            onClick={goPrev}
            disabled={idx <= 1}
            className="btn-ghost text-[13px] disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ArrowLeft size={14} />
            Précédent
          </button>

          <button
            type="button"
            onClick={isNumeric ? commitNumeric : () => goNext()}
            disabled={!canGoNext}
            className="btn-ghost text-[13px] disabled:opacity-30 disabled:hover:bg-transparent"
          >
            {idx >= 20 ? "Terminer" : "Suivant"}
            <ArrowRight size={14} />
          </button>
        </div>
      </footer>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Composants utilitaires                                                    */
/* -------------------------------------------------------------------------- */

function NumericInput({
  value,
  onChange,
  onSubmit,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
}) {
  return (
    <div className="space-y-3">
      <input
        type="number"
        inputMode="decimal"
        autoFocus
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSubmit()}
        placeholder="0"
        className="w-full px-0 py-4 bg-transparent
                   border-0 border-b border-line
                   font-serif text-[48px] leading-none text-ink
                   placeholder:text-ink-mute placeholder:font-light
                   focus:outline-none focus:border-ink
                   transition-colors duration-200"
      />
      <p className="text-[12px] text-ink-mute">
        Saisissez une valeur en heures (ex. <span className="tabular">8</span>)
      </p>
    </div>
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex items-center justify-center min-w-[20px] h-[20px]
                    px-1.5 mx-0.5 font-mono text-[10px] font-medium
                    bg-bone-card border border-line rounded text-ink-soft">
      {children}
    </kbd>
  );
}
