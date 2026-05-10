import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, Download, Mail } from "lucide-react";

export function ReportView() {
  const { reportId } = useParams();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line">
        <div className="container flex items-center justify-between py-5">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="font-serif text-[18px] font-medium tracking-tight text-ink">
              Nexus
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-clay">
              Diagnostix
            </span>
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
          <span className="pill pill-clay mb-6">Rapport — Aperçu</span>
          <h1 className="font-serif font-light leading-[1.05] tracking-tight
                         text-[clamp(2.5rem,6vw,5rem)] text-balance">
            Votre <em className="text-clay font-extralight">diagnostic</em>{" "}
            est prêt.
          </h1>
          <p className="mt-6 text-[16px] text-ink-soft max-w-2xl leading-relaxed">
            L’interface de visualisation premium (jauges animées, matrice de
            risques, recommandations IA) sera implémentée au Sprint 10. La
            génération du PDF est branchée au Sprint 7. Les données affichées
            ci-dessous sont représentatives du rendu final.
          </p>
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
                47
              </span>
              <span className="font-serif text-[40px] text-ink-mute font-light">
                / 100
              </span>
            </div>
            <hr className="rule-clay mt-8" />
            <p className="mt-4 text-[13px] text-ink-soft">
              Niveau de maturité —{" "}
              <span className="font-medium text-ink uppercase tracking-wider">
                Émergent
              </span>
            </p>
          </div>

          <div className="col-span-12 md:col-span-6 grid grid-cols-2 gap-px bg-line">
            <SubScore label="Fiscalité" value={60} />
            <SubScore label="Sociale" value={40} />
            <SubScore label="Conformité" value={50} />
            <SubScore label="Digitale" value={35} />
          </div>
        </motion.section>

        {/* Risques chiffrés */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mt-24"
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
              <span className="text-ink">18&nbsp;500&nbsp;000</span>{" "}
              <span className="text-clay">FCFA</span>
            </div>
            <p className="mt-6 text-[14px] text-ink-soft max-w-2xl">
              Estimation cumulative des risques de redressement CNPS et DGI
              identifiés par notre moteur d’analyse, sur la base de vos
              réponses et des barèmes en vigueur.
            </p>
          </div>
        </motion.section>

        {/* Actions */}
        <div className="mt-20 flex flex-wrap gap-4">
          <button className="btn-clay">
            <Download size={16} />
            Télécharger le PDF
          </button>
          <button className="btn-ghost border border-line">
            <Mail size={16} />
            Recevoir par email
          </button>
          <button className="btn-ghost border border-line">
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
          {value}
        </span>
        <span className="text-[12px] text-ink-mute">/100</span>
      </div>
      <div className="mt-4 progress-track">
        <div className="progress-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
