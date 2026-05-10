import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="font-serif text-clay text-[clamp(8rem,20vw,16rem)] leading-none font-light italic">
        404
      </div>
      <hr className="rule-clay mt-8" />
      <h1 className="mt-8 font-serif text-[28px] font-light tracking-tight text-center">
        Cette page n'existe pas.
      </h1>
      <p className="mt-4 text-[14px] text-ink-soft text-center max-w-md">
        Le lien que vous avez suivi est peut-être incorrect, ou la page a été
        retirée.
      </p>
      <Link to="/" className="btn-ghost mt-10 border border-line">
        <ArrowLeft size={14} />
        Retour à l'accueil
      </Link>
    </div>
  );
}
