import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, ShieldCheck, BarChart2, Zap, FileText, CheckCircle2 } from "lucide-react";

/* Palette OpenLab */
const OL = {
  orange: "#FF5500",
  dark:   "#CC3300",
  ink:    "#0A0A0A",
  mute:   "#888888",
  soft:   "#3D3D3D",
  line:   "#E5E5E5",
  bg:     "#F5F5F5",
};

const fade = (delay = 0) => ({
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] },
});

const fadeInView = (delay = 0) => ({
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.55, delay },
});

export function Landing() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />
      <Hero />
      <Metrics />
      <Method />
      <Proof />
      <CTA />
      <Footer />
    </div>
  );
}

/* ─────────────────────── Logo ────────────────────────────────────────────── */
function Logo({ inverted = false, size = "md" }: { inverted?: boolean; size?: "sm" | "md" | "lg" }) {
  const h = size === "sm" ? "h-8" : size === "lg" ? "h-20 sm:h-24" : "h-16 sm:h-20";
  return (
    <Link to="/" className="flex items-center gap-3 group shrink-0" aria-label="OpenLab Consulting — accueil">
      <img
        src="/openlab.png"
        alt="OpenLab Consulting"
        className={`${h} w-auto max-w-[280px] object-contain ${inverted ? "brightness-0 invert" : ""} group-hover:opacity-80 transition-opacity duration-200`}
      />
    </Link>
  );
}

/* ─────────────────────── Header ──────────────────────────────────────────── */
function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[#E5E5E5] bg-white/95 backdrop-blur-md">
      <div className="container flex items-center justify-between h-20">
        <Logo />
        <nav className="flex items-center gap-1">
          <a href="#methode" className="hidden md:inline-flex btn-ghost text-[13px]">Méthode</a>
          <a href="#preuves"  className="hidden md:inline-flex btn-ghost text-[13px]">Contexte</a>
          <Link to="/admin/login" className="hidden sm:inline-flex btn-ghost text-[13px]">Admin</Link>
          <Link
            to="/diagnostic/start"
            className="ml-2 inline-flex items-center gap-1.5 px-4 py-2.5 sm:px-6 sm:py-3
                       rounded-full text-[13px] sm:text-[14px] font-semibold text-white
                       transition-all duration-200 shadow-sm"
            style={{ background: OL.orange }}
            onMouseEnter={e => (e.currentTarget.style.background = OL.dark)}
            onMouseLeave={e => (e.currentTarget.style.background = OL.orange)}
          >
            Démarrer
            <ArrowUpRight size={14} />
          </Link>
        </nav>
      </div>
    </header>
  );
}

/* ─────────────────────── Hero ────────────────────────────────────────────── */
function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-[#E5E5E5]">
      {/* Trait orange vertical */}
      <div className="absolute left-0 inset-y-0 w-1.5 rounded-r-full" style={{ background: OL.orange }} aria-hidden />

      <div className="container relative pt-10 pb-16 sm:pt-14 sm:pb-24 lg:pt-18 lg:pb-32 pl-8 sm:pl-12 lg:pl-16">

        <motion.div {...fade(0)} className="flex items-center gap-2.5 mb-6">
          <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: OL.orange }} />
          <span className="font-mono text-[11px] uppercase tracking-[0.2em]" style={{ color: OL.mute }}>
            Côte d'Ivoire · 2026
          </span>
        </motion.div>

        <motion.h1
          {...fade(0.1)}
          className="font-black leading-[0.93] tracking-[-0.04em] text-balance"
          style={{
            fontSize: "clamp(2.6rem,8vw,6.5rem)",
            fontFamily: "'Space Grotesk', sans-serif",
            color: OL.ink,
          }}
        >
          Le diagnostic RH<br />
          <span style={{ color: OL.orange }}>taillé pour</span><br />
          vos réalités.
        </motion.h1>

        <motion.div {...fade(0.25)} className="mt-7 sm:mt-10 max-w-xl">
          <p className="text-[15px] sm:text-[17px] lg:text-[18px] leading-[1.7]" style={{ color: OL.soft }}>
            Vingt questions, cinq minutes. Un rapport qui chiffre vos risques{" "}
            <strong style={{ color: OL.ink }}>CNPS & DGI</strong>,
            mesure votre gap digital et propose trois actions prioritaires
            signées par notre IA.
          </p>

          <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Link to="/diagnostic/start" className="btn-primary group text-[15px] w-full sm:w-auto justify-center sm:justify-start">
              Commencer le diagnostic gratuit
              <ArrowUpRight size={16} className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
            <span className="font-mono text-[11px] uppercase tracking-[0.15em]" style={{ color: OL.mute }}>
              ≈ 5 min · gratuit
            </span>
          </div>

          <ul className="mt-8 flex flex-col xs:flex-row sm:flex-row gap-2.5 sm:gap-6">
            {["Aucun compte requis", "Données anonymisées", "PDF premium inclus"].map(t => (
              <li key={t} className="flex items-center gap-2 text-[13px]" style={{ color: OL.mute }}>
                <CheckCircle2 size={14} style={{ color: OL.orange }} />
                {t}
              </li>
            ))}
          </ul>
        </motion.div>
      </div>
    </section>
  );
}

/* ─────────────────────── Metrics ─────────────────────────────────────────── */
function Metrics() {
  const items = [
    { n: "20",   label: "questions ciblées" },
    { n: "4",    label: "dimensions évaluées" },
    { n: "100%", label: "conforme ARTCI" },
  ];
  return (
    <div style={{ background: OL.ink }}>
      <div className="container">
        <div className="grid grid-cols-3 divide-x divide-white/10">
          {items.map(({ n, label }) => (
            <div key={label} className="py-8 sm:py-14 px-3 sm:px-10 text-center">
              <div className="tabular font-black leading-none" style={{
                fontSize: "clamp(1.75rem,5.5vw,3.5rem)",
                color: OL.orange,
              }}>
                {n}
              </div>
              <div className="mt-2 font-mono text-[9px] sm:text-[11px] uppercase tracking-[0.12em] sm:tracking-[0.15em] text-white/50 leading-tight">
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────── Method ──────────────────────────────────────────── */
function Method() {
  const steps = [
    { n: "01", icon: <FileText size={18} />, title: "Diagnostic", body: "Vingt questions précises sur la fiscalité, la conformité sociale et votre maturité digitale." },
    { n: "02", icon: <Zap size={18} />, title: "Analyse",    body: "Notre moteur croise vos réponses avec le cadre légal ivoirien et les standards du marché." },
    { n: "03", icon: <BarChart2 size={18} />, title: "Chiffrage", body: "Estimation de votre exposition financière en cas de contrôle CNPS ou DGI, en FCFA." },
    { n: "04", icon: <ArrowUpRight size={18} />, title: "Plan d'action", body: "Trois recommandations stratégiques signées par notre IA, livrées en PDF premium." },
  ];

  return (
    <section id="methode" className="border-t border-[#E5E5E5]">
      <div className="container py-20 lg:py-28">

        <div className="mb-12 lg:mb-16">
          <span className="pill">Méthode</span>
          <h2 className="mt-5 font-bold tracking-tight leading-[1.05]"
              style={{ fontSize: "clamp(1.8rem,4vw,2.8rem)", color: OL.ink }}>
            Une démarche <span style={{ color: OL.orange }}>rigoureuse</span> et documentée.
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-px bg-[#E5E5E5] rounded-xl overflow-hidden">
          {steps.map((step, i) => (
            <motion.div
              key={step.n}
              {...fadeInView(i * 0.07)}
              className="bg-white p-7 lg:p-9 min-h-[220px] flex flex-col
                         hover:bg-[#FAFAFA] transition-colors duration-200 group cursor-default"
            >
              <div className="flex items-center justify-between mb-8">
                <span className="font-mono text-[11px] tracking-[0.2em] font-bold" style={{ color: OL.orange }}>
                  {step.n}
                </span>
                <span className="transition-colors duration-200 text-[#D0D0D0] group-hover:text-[#FF5500]">
                  {step.icon}
                </span>
              </div>
              <h3 className="text-[22px] font-bold mb-2" style={{ color: OL.ink }}>{step.title}</h3>
              <p className="text-[14px] leading-relaxed mt-auto" style={{ color: OL.mute }}>{step.body}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────── Proof ───────────────────────────────────────────── */
function Proof() {
  return (
    <section id="preuves" className="border-t border-[#E5E5E5]" style={{ background: OL.bg }}>
      <div className="container py-20 lg:py-28">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">

          <motion.div {...fadeInView()}>
            <span className="pill">Pourquoi maintenant</span>
            <p className="mt-6 font-semibold leading-[1.2] tracking-tight text-balance"
               style={{ fontSize: "clamp(1.6rem,3vw,2.3rem)", color: OL.ink }}>
              La réforme fiscale{" "}
              <span style={{ color: OL.orange }}>2024</span> et la digitalisation
              des contrôles transforment la conformité RH en risque financier majeur.{" "}
              <span style={{ color: OL.mute }}>Anticiper devient un avantage décisif.</span>
            </p>
            <div className="rule-orange mt-10" />
            <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.2em]" style={{ color: OL.mute }}>
              Source — DGI Côte d'Ivoire · Annexe fiscale 2024
            </p>
          </motion.div>

          <motion.aside
            {...fadeInView(0.15)}
            className="border-l-4 pl-8 py-2 self-center"
            style={{ borderColor: OL.orange }}
          >
            <div className="tabular font-black leading-none" style={{
              fontSize: "clamp(5rem,14vw,9rem)",
              color: OL.ink,
            }}>
              80<span style={{ color: OL.orange }}>%</span>
            </div>
            <p className="mt-4 text-[15px] leading-relaxed max-w-xs" style={{ color: OL.soft }}>
              des entreprises ivoiriennes ne sont pas encore alignées sur la
              réforme IGR 2024 ou la Convention Collective Interprofessionnelle.
            </p>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────── CTA ─────────────────────────────────────────────── */
function CTA() {
  return (
    <section style={{ background: OL.orange }}>
      <div className="container py-20 lg:py-28 text-center">
        <motion.h2
          {...fadeInView()}
          className="font-black leading-[0.95] tracking-tight text-balance text-white"
          style={{ fontSize: "clamp(2.2rem,7vw,5rem)" }}
        >
          Cinq minutes pour savoir{" "}
          <span className="italic" style={{ opacity: 0.75 }}>où vous en êtes.</span>
        </motion.h2>

        <p className="mt-6 text-[16px] text-white/75 max-w-md mx-auto leading-relaxed">
          Aucune création de compte. Aucune donnée nominative.
          Le rapport est à vous, immédiatement.
        </p>

        <motion.div {...fadeInView(0.15)} className="mt-10">
          <Link
            to="/diagnostic/start"
            className="inline-flex items-center gap-2 px-8 py-4 sm:px-10 sm:py-5
                       text-[15px] font-bold rounded-full shadow-xl
                       transition-all duration-200 hover:-translate-y-0.5"
            style={{ background: OL.ink, color: "#fff" }}
            onMouseEnter={e => (e.currentTarget.style.background = "#1a1a1a")}
            onMouseLeave={e => (e.currentTarget.style.background = OL.ink)}
          >
            Démarrer maintenant
            <ArrowUpRight size={18} />
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

/* ─────────────────────── Footer ──────────────────────────────────────────── */
function Footer() {
  return (
    <footer style={{ background: OL.ink }} className="text-white">
      <div className="container py-12 sm:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-16">

          <div>
            <Logo inverted size="md" />
            <p className="mt-5 text-[13px] leading-relaxed text-white/50 max-w-xs">
              Édité par <strong className="font-semibold text-white">OpenLab Consulting</strong>.
              Solution NexusRH — Côte d'Ivoire.
            </p>
          </div>

          <div>
            <div className="flex items-start gap-3">
              <ShieldCheck size={15} className="shrink-0 mt-0.5" style={{ color: OL.orange }} />
              <p className="text-[12px] leading-[1.75] text-white/50">
                Conformément à la Loi n°2013-450 relative à la protection des données
                à caractère personnel en Côte d'Ivoire, les informations collectées
                sont traitées de manière anonyme. Aucune donnée nominative n'est stockée.
                Droit d'accès et suppression :{" "}
                <a
                  href="mailto:dpo@openlabconsulting.com"
                  className="underline-offset-2 hover:underline transition-colors"
                  style={{ color: OL.orange }}
                >
                  dpo@openlabconsulting.com
                </a>.
              </p>
            </div>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/25 mt-8">
              © 2026 OpenLab Consulting · Abidjan, Côte d'Ivoire
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
