import { useParams } from "react-router-dom";

export function Generating() {
  const { sessionId } = useParams();
  return (
    <div className="container mx-auto max-w-xl px-4 py-24 text-center">
      <div className="mx-auto h-16 w-16 animate-spin rounded-full border-4 border-nexus-orange border-t-transparent" />
      <h1 className="mt-8 font-display text-2xl font-bold">Génération de votre rapport…</h1>
      <p className="mt-2 text-nexus-gray-dark">Session {sessionId}</p>
    </div>
  );
}
