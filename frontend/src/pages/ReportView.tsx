import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, Download, Loader2, Mail } from "lucide-react";
import { api } from "@/lib/api";

interface ReportData {
  report_id: string;
  status: string;
  global_score: number | null;
  maturity_level: string | null;
  scores_by_category: Record<string, number> | null;
  risk_score: number | null;
  financial_exposure_fcfa: number | null;
  digital_gap_pct: number | null;
  executive_summary: string | null;
  risks_detected: Array<{ id: string; title: string; severity: string; fcfa_impact: number }> | null;
  recommendations: Array<{
    priority: number;
    title: string;
    description: string;
    expected_gain_fcfa: number;
    implementation_weeks: number;
    nexusrh_module: string;
  }> | null;
  pdf_url: string | null;
}

const MATURITY_COLORS: Record<string, string> = {
  CRITIQUE: "text-red-600",
  EMERGENT: "text-orange-500",
  STRUCTURE: "text-yellow-600",
  OPTIMISE: "text-green-600",
  IA_NATIVE: "text-emerald-600",
};

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "bg-red-50 border-red-500 text-red-700",
  HIGH: "bg-orange-50 border-orange-400 text-orange-700",
  MEDIUM: "bg-yellow-50 border-yellow-400 text-yellow-700",
  LOW: "bg-green-50 border-green-400 text-green-700",
};

export function ReportView() {
  const { reportId } = useParams();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [emailSent, setEmailSent] = useState(false);

  useEffect(() => {
    if (!reportId) return;
    api
      .get<ReportData>(`/reports/${reportId}`)
      .then((r) => {
        setReport(r);
        setLoading(false);
      })
      .catch((err) => {
        setError(err?.detail ?? "Rapport introuvable.");
        setLoading(false);
      });
  }, [reportId]);

  async function handleSendEmail() {
    if (!reportId) return;
    try {
      await api.post(`/reports/${reportId}/send`);
      setEmailSent(true);
    } catch {
      // silent — user can retry
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-clay" size={32} />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 text-center">
        <p role="alert" className="text-[16px] text-ink-soft">
          {error ?? "Rapport introuvable."}
        </p>
      </div>
    );
  }

  const score = report.global_score ?? 0;
  const maturity = report.maturity_level ?? "";
  const categories = report.scores_by_category ?? {};

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line bg-white sticky top-0 z-30">
        <div className="container flex items-center justify-between h-[72px]">
          <Link to="/">
            <img src="/openlab.png" alt="OpenLab" className="h-11 sm:h-12 w-auto" />
          </Link>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute">
            Rapport · {reportId?.slice(0, 14)}
          </span>
        </div>
      </header>

      <main className="container py-16 lg:py-24 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="pill pill-clay mb-6">Rapport — Résultats</span>
          <h1 className="font-serif font-light leading-[1.05] tracking-tight
                         text-[clamp(2.5rem,6vw,5rem)] text-balance">
            Votre <em className="text-clay font-extralight">diagnostic</em>{" "}
            est prêt.
          </h1>
        </motion.div>

        {/* Score principal */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="mt-16 grid grid-cols-12 gap-8 lg:gap-16 items-end"
        >
          <div className="col-span-12 md:col-span-6">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute">
              Score global
            </span>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="font-serif tabular text-[120px] lg:text-[160px]
                               leading-none font-medium text-ink">
                {Math.round(score)}
              </span>
              <span className="font-serif text-[40px] text-ink-mute font-light">
                / 100
              </span>
            </div>
            <hr className="rule-clay mt-8" />
            <p className="mt-4 text-[13px] text-ink-soft">
              Niveau de maturité —{" "}
              <span className={`font-medium uppercase tracking-wider ${MATURITY_COLORS[maturity] ?? "text-ink"}`}>
                {maturity}
              </span>
            </p>
          </div>

          <div className="col-span-12 md:col-span-6 grid grid-cols-2 gap-px bg-line">
            {Object.entries(categories).map(([label, value]) => (
              <SubScore key={label} label={label} value={value} />
            ))}
          </div>
        </motion.section>

        {/* Résumé IA */}
        {report.executive_summary && (
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mt-16 paper p-10"
          >
            <h2 className="font-serif text-[22px] font-light mb-4">Synthèse experte</h2>
            <p className="text-[15px] leading-relaxed text-ink-soft">
              {report.executive_summary}
            </p>
          </motion.section>
        )}

        {/* Exposition financière */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mt-12"
        >
          <div className="flex items-baseline justify-between mb-8">
            <h2 className="font-serif text-[32px] font-light tracking-tight">
              Exposition financière estimée
            </h2>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute">
              en cas de contrôle
            </span>
          </div>

          <div className="paper p-10 lg:p-12">
            <div className="font-serif tabular text-[clamp(3rem,8vw,5.5rem)]
                            font-medium leading-none">
              <span className="text-ink">
                {(report.financial_exposure_fcfa ?? 0).toLocaleString("fr-FR")}
              </span>{" "}
              <span className="text-clay">FCFA</span>
            </div>
            <p className="mt-6 text-[14px] text-ink-soft max-w-2xl">
              Estimation cumulative des risques de redressement CNPS et DGI
              identifiés par notre moteur d'analyse, sur la base de vos
              réponses et des barèmes en vigueur.
            </p>
          </div>
        </motion.section>

        {/* Risques */}
        {report.risks_detected && report.risks_detected.length > 0 && (
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mt-12"
          >
            <h2 className="font-serif text-[32px] font-light tracking-tight mb-8">
              Risques identifiés
            </h2>
            <div className="space-y-3">
              {report.risks_detected.map((risk) => (
                <div
                  key={risk.id}
                  className={`border-l-4 p-4 rounded-r ${SEVERITY_COLORS[risk.severity] ?? "bg-gray-50 border-gray-400 text-gray-700"}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-[15px]">{risk.title}</span>
                    <span className="text-[11px] uppercase tracking-wider font-bold">
                      {risk.severity}
                    </span>
                  </div>
                  <p className="text-[13px] mt-1 opacity-80">
                    Impact estimé : {risk.fcfa_impact.toLocaleString("fr-FR")} FCFA
                  </p>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {/* Recommandations */}
        {report.recommendations && report.recommendations.length > 0 && (
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mt-12"
          >
            <h2 className="font-serif text-[32px] font-light tracking-tight mb-8">
              Recommandations stratégiques
            </h2>
            <div className="space-y-4">
              {report.recommendations.map((reco) => (
                <div key={reco.priority} className="paper p-6">
                  <div className="flex items-start gap-4">
                    <span className="flex-shrink-0 w-8 h-8 rounded-full bg-clay text-bone
                                     flex items-center justify-center font-bold text-[14px]">
                      {reco.priority}
                    </span>
                    <div className="flex-1">
                      <div className="font-medium text-[16px] text-ink">{reco.title}</div>
                      <div className="text-[12px] text-ink-mute mt-1">
                        {reco.nexusrh_module} · {reco.implementation_weeks} semaines
                      </div>
                      <p className="mt-2 text-[14px] text-ink-soft">{reco.description}</p>
                      <div className="mt-3 inline-block text-[12px] font-medium
                                      bg-green-50 text-green-700 px-3 py-1 rounded">
                        Gain estimé : {reco.expected_gain_fcfa.toLocaleString("fr-FR")} FCFA
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {/* Actions */}
        <div className="mt-20 flex flex-wrap gap-4">
          {report.pdf_url && (
            <a
              href={report.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-clay"
            >
              <Download size={16} />
              Télécharger le PDF
            </a>
          )}
          <button
            type="button"
            onClick={handleSendEmail}
            disabled={emailSent}
            className="btn-ghost border border-line disabled:opacity-50"
          >
            <Mail size={16} />
            {emailSent ? "Email envoyé !" : "Recevoir par email"}
          </button>
          <button
            type="button"
            className="btn-ghost border border-line"
            onClick={() => window.open("https://nexusrh.ci/demo", "_blank")}
          >
            <ArrowUpRight size={16} />
            Demander une démo NexusRH
          </button>
        </div>
      </main>
    </div>
  );
}

function SubScore({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-bone-card p-6">
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-3">
        {label}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="font-serif tabular text-[36px] font-medium text-ink leading-none">
          {Math.round(value)}
        </span>
        <span className="text-[12px] text-ink-mute">/100</span>
      </div>
      <div className="mt-4 progress-track">
        <div className="progress-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
