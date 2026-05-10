import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight, ChevronDown, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface Question {
  id: number;
  code: string;
  label: string;
  category: "FISCALE" | "SOCIALE" | "CONFORMITE" | "DIGITALE";
  answer_type: "YES_NO" | "YES_NO_PARTIAL" | "YES_NO_MANUAL" | "FREE_NUMERIC";
  help_text: string | null;
}

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
        { value: "NO", label: "Non", shortcut: "2" },
      ];
    case "YES_NO_PARTIAL":
      return [
        { value: "YES", label: "Oui", shortcut: "1", helper: "Pleinement en place" },
        { value: "PARTIAL", label: "Partiellement", shortcut: "2", helper: "Mise en place en cours" },
        { value: "NO", label: "Non", shortcut: "3", helper: "Pas encore" },
      ];
    case "YES_NO_MANUAL":
      return [
        { value: "YES", label: "Oui, automatisé", shortcut: "1" },
        { value: "MANUAL", label: "Calculé manuellement", shortcut: "2", helper: "Excel, papier ou calcul à la main" },
        { value: "NO", label: "Non géré", shortcut: "3" },
      ];
    case "FREE_NUMERIC":
      return [];
  }
}

export function Questionnaire() {
  const navigate = useNavigate();
  const { sessionId, questionIndex } = useParams();
  const idx = Math.max(1, parseInt(questionIndex ?? "1", 10));

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [numericValue, setNumericValue] = useState<string>("");
  const [direction, setDirection] = useState<1 | -1>(1);

  useEffect(() => {
    api
      .get<{ questions: Question[] }>(`/sessions/${sessionId}/questions`)
      .then((r) => {
        setQuestions(r.questions);
        setLoadingQuestions(false);
      })
      .catch(() => setLoadingQuestions(false));
  }, [sessionId]);

  const question = questions[idx - 1] ?? null;
  const total = questions.length || 20;
  const options = useMemo(
    () => (question ? getOptions(question.answer_type) : []),
    [question]
  );
  const isNumeric = question?.answer_type === "FREE_NUMERIC";
  const currentAnswer = question ? (answers[question.id] ?? "") : "";
  const canGoNext = isNumeric
    ? numericValue !== "" && !isNaN(Number(numericValue))
    : currentAnswer !== "";

  useEffect(() => {
    if (isNumeric && question) {
      setNumericValue(answers[question.id] ?? "");
    }
  }, [question?.id, isNumeric, answers, question]);

  async function saveResponse(questionId: number, value: string, isNum = false) {
    try {
      await api.post(`/sessions/${sessionId}/responses`, {
        question_id: questionId,
        answer_value: isNum ? "FREE_NUMERIC" : value,
        answer_numeric: isNum ? parseFloat(value) : null,
      });
    } catch {
      // silent — non-blocking
    }
  }

  function selectAnswer(value: string) {
    if (!question) return;
    setAnswers((prev) => ({ ...prev, [question.id]: value }));
    saveResponse(question.id, value);
    window.setTimeout(() => goNext(value), 250);
  }

  function commitNumeric() {
    if (!canGoNext || !question) return;
    setAnswers((prev) => ({ ...prev, [question.id]: numericValue }));
    saveResponse(question.id, numericValue, true);
    goNext(numericValue);
  }

  function goNext(_value?: string) {
    setDirection(1);
    if (idx >= total) {
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

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (!question) return;
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
  }, [idx, isNumeric, canGoNext, options, numericValue, question]);

  if (loadingQuestions) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-clay" size={32} />
      </div>
    );
  }

  if (!question) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <p className="text-[16px] text-ink-soft">Question introuvable.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line bg-white sticky top-0 z-30">
        <div className="container flex items-center justify-between h-[72px]">
          <Link to="/">
            <img src="/openlab.png" alt="OpenLab" className="h-11 sm:h-12 w-auto" />
          </Link>

          <div className="flex items-center gap-6">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute">
              {CATEGORY_LABELS[question.category]}
            </span>
            <span className="tabular text-[12px] text-ink-soft">
              <span className="text-ink font-medium">{idx}</span>
              <span className="text-ink-mute mx-1">/</span>
              <span className="text-ink-mute">{total}</span>
            </span>
          </div>
        </div>
        <div className="progress-track">
          <motion.div
            className="progress-fill"
            initial={false}
            animate={{ width: `${(idx / total) * 100}%` }}
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
            <div className="hidden md:block md:col-span-3 lg:col-span-3">
              <div className="sticky top-[88px]">
                <div className="question-number text-[clamp(8rem,18vw,16rem)]">
                  {String(idx).padStart(2, "0")}
                </div>
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mt-2 ml-2">
                  {question.code}
                </div>
              </div>
            </div>

            <div className="col-span-12 md:col-span-9 lg:col-start-5 lg:col-span-8">
              <div className="md:hidden mb-6">
                <span className="font-mono text-[11px] tracking-[0.2em] text-clay">
                  Question {idx} · {String(idx).padStart(2, "0")} / {total}
                </span>
              </div>

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

              <p className="mt-8 text-[11px] text-ink-mute">
                {isNumeric ? (
                  <>Appuyez sur <Kbd>Entrée</Kbd> pour valider</>
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
            {idx >= total ? "Terminer" : "Suivant"}
            <ArrowRight size={14} />
          </button>
        </div>
      </footer>
    </div>
  );
}

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
