import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, ShieldCheck } from "lucide-react";

export function Landing() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <Hero />
      <Method />
      <Proof />
      <CTA />
      <Footer />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Header                                                                    */
/* -------------------------------------------------------------------------- */

function Header() {
  return (
    <header className="border-b border-line">
      <div className="container flex items-center justify-between py-5">
        <Link to="/" className="flex items-baseline gap-2">
          <span className="font-serif text-[22px] font-medium tracking-tight text-ink">
            Nexus
          </span>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-clay">
            Diagnostix
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          <a
            href="#methode"
            className="hidden sm:inline-flex btn-ghost text-[13px]"
          >
            Méthode
          </a>
          <a
            href="#preuves"
            className="hidden sm:inline-flex btn-ghost text-[13px]"
          >
            Pourquoi
          </a>
          <Link to="/admin/login" className="btn-ghost text-[13px]">
            Admin
          </Link>
        </nav>
      </div>
    </header>
  );
}

/* -------------------------------------------------------------------------- */
/*  Hero — split asymétrique, typographie éditoriale                          */
/* -------------------------------------------------------------------------- */

function Hero() {
  return (
    <section className="container relative pt-20 lg:pt-32 pb-24 lg:pb-40">
      {/* Petit méta-badge */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <span className="pill pill-clay">
          <span>Édition Côte d’Ivoire · 2026</span>
        </span>
      </motion.div>

      {/* Titre éditorial */}
      <motion.h1
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        className="hero-headline mt-10 text-[clamp(2.75rem,7.5vw,6.5rem)] max-w-5xl text-balance"
      >
        Le diagnostic RH&nbsp;
        <em>vraiment</em> taillé
        <br />
        pour vos réalités.
      </motion.h1>

      {/* Bloc inférieur en deux colonnes */}
      <div className="mt-16 lg:mt-24 grid grid-cols-12 gap-8 lg:gap-16 items-end">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="col-span-12 md:col-span-7 lg:col-span-6"
        >
          <p className="text-[19px] leading-[1.55] text-ink-soft text-pretty">
            Vingt questions, cinq minutes. Un rapport qui chiffre vos risques de
            redressement <span className="text-ink font-medium">CNPS</span> et{" "}
            <span className="text-ink font-medium">DGI</span>, mesure votre écart
            au standard&nbsp;IA-Native, et propose trois actions prioritaires
            signées par notre IA experte du droit ivoirien.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link to="/diagnostic/start" className="btn-clay group">
              Commencer le diagnostic
              <ArrowUpRight
                size={18}
                className="transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              />
            </Link>
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-ink-mute">
              ≈ 5 min · gratuit · sans engagement
            </span>
          </div>
        </motion.div>

        {/* Colonne droite : indicateurs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="col-span-12 md:col-span-5 lg:col-start-9 lg:col-span-4
                     border-l border-line pl-8 space-y-6"
        >
          <Indicator value="20" suffix="questions" />
          <Indicator value="4" suffix="dimensions évaluées" />
          <Indicator value="100%" suffix="conforme ARTCI" />
        </motion.div>
      </div>
    </section>
  );
}

function Indicator({ value, suffix }: { value: string; suffix: string }) {
  return (
    <div>
      <div className="flex items-baseline gap-2">
        <span className="tabular text-[36px] font-medium text-ink leading-none">
          {value}
        </span>
      </div>
      <div className="mt-1 text-[13px] text-ink-mute">{suffix}</div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Méthode — 4 cartes éditoriales numérotées                                 */
/* -------------------------------------------------------------------------- */

function Method() {
  const steps = [
    {
      n: "01",
      title: "Diagnostic",
      body: "Vingt questions précises sur la fiscalité, la conformité sociale et votre maturité digitale.",
    },
    {
      n: "02",
      title: "Analyse",
      body: "Notre moteur croise vos réponses avec le cadre légal ivoirien et les standards du marché.",
    },
    {
      n: "03",
      title: "Chiffrage",
      body: "Estimation de votre exposition financière en cas de contrôle, en francs CFA.",
    },
    {
      n: "04",
      title: "Plan d’action",
      body: "Trois recommandations stratégiques signées par notre IA, livrées en PDF premium.",
    },
  ];

  return (
    <section id="methode" className="border-t border-line bg-bone-card">
      <div className="container py-24 lg:py-32">
        <div className="grid grid-cols-12 gap-8 lg:gap-12 mb-16">
          <div className="col-span-12 md:col-span-3">
            <span className="pill">Méthode</span>
          </div>
          <h2 className="col-span-12 md:col-span-9 font-serif font-light
                         text-[clamp(2rem,4vw,3.5rem)] leading-[1.05]
                         tracking-tight text-balance">
            Une démarche sobre,{" "}
            <span className="italic text-clay font-extralight">rigoureuse,</span>{" "}
            <span className="italic font-extralight">documentée.</span>
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-line">
          {steps.map((step, i) => (
            <motion.div
              key={step.n}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="bg-bone-card p-8 lg:p-10 min-h-[280px] flex flex-col"
            >
              <div className="font-mono text-[11px] tracking-[0.2em] text-clay mb-12">
                {step.n}
              </div>
              <h3 className="font-serif text-[28px] font-normal mb-3 text-ink">
                {step.title}
              </h3>
              <p className="text-[15px] leading-relaxed text-ink-soft mt-auto">
                {step.body}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Proof — gros chiffre + citation, ton éditorial                            */
/* -------------------------------------------------------------------------- */

function Proof() {
  return (
    <section id="preuves" className="border-t border-line">
      <div className="container py-24 lg:py-32 grid grid-cols-12 gap-8 lg:gap-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="col-span-12 md:col-span-7"
        >
          <span className="pill mb-8">Pourquoi maintenant</span>
          <p className="font-serif text-[clamp(1.75rem,3vw,2.75rem)]
                        leading-[1.15] tracking-tight font-light text-balance">
            La réforme fiscale&nbsp;<em className="text-clay">2024</em> et la
            digitalisation accélérée des contrôles transforment la conformité RH
            en risque financier majeur.{" "}
            <span className="text-ink-soft">
              Anticiper devient un avantage stratégique décisif.
            </span>
          </p>

          <hr className="rule-clay mt-12" />
          <p className="mt-6 font-mono text-[11px] uppercase tracking-[0.2em] text-ink-mute">
            Source — DGI Côte d’Ivoire, Annexe fiscale 2024
          </p>
        </motion.div>

        <motion.aside
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, delay: 0.2 }}
          className="col-span-12 md:col-span-5 md:col-start-8
                     border-l border-line pl-8 self-end"
        >
          <div className="tabular text-[88px] lg:text-[120px] font-medium leading-none text-ink">
            80<span className="text-clay">%</span>
          </div>
          <p className="mt-4 text-[14px] leading-relaxed text-ink-soft">
            des entreprises ivoiriennes ne sont pas encore alignées sur la
            réforme&nbsp;IGR&nbsp;2024 ou la Convention Collective
            Interprofessionnelle.
          </p>
        </motion.aside>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  CTA final                                                                 */
/* -------------------------------------------------------------------------- */

function CTA() {
  return (
    <section className="border-t border-line bg-ink text-bone">
      <div className="container py-24 lg:py-32 text-center">
        <motion.h2
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="font-serif font-light leading-[0.95] tracking-tight
                     text-[clamp(2.5rem,7vw,5.5rem)] max-w-4xl mx-auto text-balance"
        >
          Cinq minutes pour{" "}
          <span className="italic text-clay-soft">savoir où vous en êtes.</span>
        </motion.h2>

        <p className="mt-8 text-[16px] text-bone/70 max-w-xl mx-auto leading-relaxed">
          Aucune création de compte. Aucune donnée nominative. Le rapport est à
          vous, immédiatement.
        </p>

        <div className="mt-12">
          <Link
            to="/diagnostic/start"
            className="inline-flex items-center gap-2 px-8 py-4
                       text-[15px] font-medium tracking-tight rounded-full
                       bg-bone text-ink
                       hover:bg-clay hover:text-bone
                       transition-colors duration-300"
          >
            Démarrer maintenant
            <ArrowUpRight size={18} />
          </Link>
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Footer — mention légale ARTCI mot pour mot                                */
/* -------------------------------------------------------------------------- */

function Footer() {
  return (
    <footer className="border-t border-line bg-bone-dark mt-auto">
      <div className="container py-16 grid grid-cols-12 gap-8">
        <div className="col-span-12 md:col-span-5">
          <div className="flex items-baseline gap-2 mb-6">
            <span className="font-serif text-[18px] font-medium tracking-tight text-ink">
              Nexus
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-clay">
              Diagnostix
            </span>
          </div>
          <p className="text-[13px] leading-relaxed text-ink-soft max-w-sm">
            Édité par <strong className="font-medium text-ink">OpenLab Consulting</strong>.
            Solution NexusRH — Côte d’Ivoire.
          </p>
        </div>

        <div className="col-span-12 md:col-span-7 md:col-start-6">
          <div className="flex items-start gap-3 mb-6">
            <ShieldCheck size={16} className="text-clay flex-shrink-0 mt-0.5" />
            <p className="text-[12px] leading-[1.7] text-ink-soft text-pretty">
              Conformément à la Loi n°2013-450 relative à la protection des données à
              caractère personnel en Côte d’Ivoire, les informations collectées dans
              ce diagnostic sont traitées de manière anonyme à des fins d’analyse
              statistique. Aucune donnée nominative n’est stockée. Vous disposez d’un
              droit d’accès et de suppression via{" "}
              <a
                href="mailto:dpo@openlabconsulting.com"
                className="text-clay underline-offset-2 hover:underline"
              >
                dpo@openlabconsulting.com
              </a>.
            </p>
          </div>

          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mt-8">
            © 2026 OpenLab Consulting · Abidjan
          </p>
        </div>
      </div>
    </footer>
  );
}
