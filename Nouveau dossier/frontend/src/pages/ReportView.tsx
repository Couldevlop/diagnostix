import { useParams } from "react-router-dom";

export function ReportView() {
  const { reportId } = useParams();
  return (
    <div className="container mx-auto max-w-4xl px-4 py-16">
      <h1 className="font-display text-3xl font-bold">Votre rapport Nexus-Diagnostix</h1>
      <p className="mt-2 text-nexus-gray-dark">Rapport <code>{reportId}</code></p>
      <p className="mt-6 text-nexus-gray-dark">
        L'affichage premium (jauges, charts, recommandations IA) sera implémenté au Sprint 10
        (cf. CLAUDE.md §9.2).
      </p>
    </div>
  );
}
