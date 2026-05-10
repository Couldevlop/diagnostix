import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldCheck, BarChart3, Brain } from "lucide-react";

export function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-nexus-gray">
      {/* Header */}
      <header className="container mx-auto flex items-center justify-between py-6">
        <div className="flex items-center gap-2">
          <div className="h-10 w-10 rounded-lg bg-nexus-orange" aria-hidden="true" />
          <span className="font-display text-xl font-bold">NexusRH</span>
        </div>
        <Link
          to="/admin/login"
          className="text-sm text-nexus-gray-dark hover:text-nexus-black"
        >
          Espace admin →
        </Link>
      </header>

      {/* Hero */}
      <main className="container mx-auto px-4 py-16 md:py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2 text-sm font-medium text-accent-foreground">
            <ShieldCheck className="h-4 w-4" />
            Conforme ARTCI · Données 100 % anonymes
          </div>

          <h1 className="font-display text-4xl font-bold leading-tight tracking-tight text-nexus-black md:text-6xl">
            Évaluez la maturité digitale RH de votre entreprise{" "}
            <span className="text-nexus-orange">en 5 minutes</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-nexus-gray-dark">
            Nexus-Diagnostix analyse votre conformité fiscale (IGR 2024), sociale (CNPS,
            Convention Collective) et votre transformation digitale, puis génère un rapport
            personnalisé avec vos risques chiffrés et 3 recommandations stratégiques.
          </p>

          <div className="mt-10">
            <Link to="/diagnostic/start" className="btn-primary text-lg">
              Démarrer mon diagnostic gratuit →
            </Link>
          </div>
        </motion.div>

        {/* Bénéfices */}
        <section className="mx-auto mt-24 grid max-w-5xl gap-6 md:grid-cols-3">
          <BenefitCard
            icon={<BarChart3 className="h-8 w-8 text-nexus-orange" />}
            title="Risques chiffrés"
            description="Identifiez votre exposition financière en cas de redressement CNPS ou DGI, en FCFA."
          />
          <BenefitCard
            icon={<Brain className="h-8 w-8 text-nexus-orange" />}
            title="Analyse IA experte"
            description="Notre IA spécialisée droit ivoirien interprète vos réponses et personnalise les recommandations."
          />
          <BenefitCard
            icon={<ShieldCheck className="h-8 w-8 text-nexus-orange" />}
            title="Plan d'action prioritaire"
            description="Recevez un rapport PDF premium avec 3 actions concrètes pour moderniser votre RH."
          />
        </section>
      </main>

      {/* Footer — mentions légales (Loi ARTCI 2013-450) */}
      <footer className="mt-24 border-t border-border bg-nexus-black py-12 text-sm text-nexus-gray">
        <div className="container mx-auto px-4">
          <p className="mx-auto max-w-3xl text-center leading-relaxed">
            Conformément à la Loi n°2013-450 relative à la protection des données à caractère
            personnel en Côte d'Ivoire, les informations collectées dans ce diagnostic sont
            traitées de manière anonyme à des fins d'analyse statistique. Aucune donnée
            nominative n'est stockée. Vous disposez d'un droit d'accès et de suppression via{" "}
            <a
              href="mailto:dpo@openlabconsulting.com"
              className="text-nexus-orange hover:underline"
            >
              dpo@openlabconsulting.com
            </a>
            .
          </p>
          <p className="mt-6 text-center text-xs opacity-60">
            © 2026 OpenLab Consulting · NexusRH CI · www.openlabconsulting.com
          </p>
        </div>
      </footer>
    </div>
  );
}

interface BenefitCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

function BenefitCard({ icon, title, description }: BenefitCardProps) {
  return (
    <div className="card-elevated">
      <div className="mb-4">{icon}</div>
      <h3 className="font-display text-xl font-semibold">{title}</h3>
      <p className="mt-2 text-nexus-gray-dark">{description}</p>
    </div>
  );
}
