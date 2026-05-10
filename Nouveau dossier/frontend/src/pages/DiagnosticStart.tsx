import { Link } from "react-router-dom";

export function DiagnosticStart() {
  return (
    <div className="container mx-auto max-w-2xl px-4 py-16">
      <h1 className="font-display text-3xl font-bold">Avant de commencer</h1>
      <p className="mt-2 text-nexus-gray-dark">
        Quelques informations pour personnaliser votre diagnostic. Aucune donnée nominative
        n'est conservée sans votre consentement explicite.
      </p>

      <div className="mt-8 rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-nexus-gray-dark">
          Le formulaire complet sera implémenté au Sprint 10 (cf. CLAUDE.md §14).
        </p>
        <Link to="/" className="btn-secondary mt-6 inline-flex">
          ← Retour à l'accueil
        </Link>
      </div>
    </div>
  );
}
