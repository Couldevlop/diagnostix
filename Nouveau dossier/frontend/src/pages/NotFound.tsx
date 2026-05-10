import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="container mx-auto max-w-xl px-4 py-24 text-center">
      <p className="font-display text-6xl font-bold text-nexus-orange">404</p>
      <h1 className="mt-4 font-display text-2xl font-bold">Page introuvable</h1>
      <p className="mt-2 text-nexus-gray-dark">
        La page que vous cherchez n'existe pas ou a été déplacée.
      </p>
      <Link to="/" className="btn-primary mt-8 inline-flex">
        Retour à l'accueil
      </Link>
    </div>
  );
}
