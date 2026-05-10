import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-white">
      <img src="/openlab.png" alt="OpenLab" className="h-10 w-auto mb-12 opacity-80" />
      <div className="tabular font-black leading-none text-clay" style={{ fontSize: "clamp(7rem,20vw,14rem)" }}>
        404
      </div>
      <div className="rule-orange mt-6 mx-auto" />
      <h1 className="mt-6 font-bold text-[24px] tracking-tight text-center text-ink">
        Cette page n'existe pas.
      </h1>
      <p className="mt-3 text-[14px] text-ink-mute text-center max-w-sm leading-relaxed">
        Le lien que vous avez suivi est peut-être incorrect ou la page a été retirée.
      </p>
      <Link to="/" className="btn-ghost mt-8 border border-line flex items-center gap-1.5">
        <ArrowLeft size={14} />
        Retour à l'accueil
      </Link>
    </div>
  );
}
