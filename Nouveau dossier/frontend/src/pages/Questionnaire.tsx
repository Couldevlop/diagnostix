import { useParams } from "react-router-dom";

export function Questionnaire() {
  const { sessionId, questionIndex } = useParams();
  return (
    <div className="container mx-auto max-w-2xl px-4 py-16">
      <h1 className="font-display text-2xl font-bold">Questionnaire</h1>
      <p className="mt-2 text-sm text-nexus-gray-dark">
        Session <code>{sessionId}</code> — question {questionIndex} / 20
      </p>
      <p className="mt-6 text-nexus-gray-dark">
        Le parcours dynamique (1 question/écran, animations, auto-save) sera implémenté au
        Sprint 10 (cf. CLAUDE.md §9.2 et §14).
      </p>
    </div>
  );
}
