import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2, LogOut } from "lucide-react";
import { api } from "@/lib/api";

interface Stats {
  total_sessions: number;
  completed_sessions: number;
  completion_rate: number;
  average_global_score: number | null;
}

interface AdminQuestion {
  id: number;
  code: string;
  label: string;
  category: string;
  weight: number;
  answer_type: string;
  order: number;
  is_active: boolean;
  help_text: string | null;
}

interface Setting {
  key: string;
  value: unknown;
  description: string | null;
}

interface Lead {
  session_id: string;
  contact_email: string;
  sector: string | null;
  company_size: string | null;
  started_at: string | null;
}

interface AuditEntry {
  id: number;
  actor_type: string;
  actor_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  created_at: string | null;
}

type Tab = "dashboard" | "questions" | "settings" | "leads" | "audit";

const TAB_LABELS: Record<Tab, string> = {
  dashboard: "Tableau de bord",
  questions: "Questions",
  settings: "Paramètres",
  leads: "Leads",
  audit: "Audit",
};

export function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");

  const [questions, setQuestions] = useState<AdminQuestion[]>([]);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [questionsLoaded, setQuestionsLoaded] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<AdminQuestion | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editWeight, setEditWeight] = useState("");
  const [editHelpText, setEditHelpText] = useState("");
  const [savingQuestion, setSavingQuestion] = useState(false);

  const [settings, setSettings] = useState<Setting[]>([]);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [editingSetting, setEditingSetting] = useState<Setting | null>(null);
  const [editSettingValue, setEditSettingValue] = useState("");
  const [savingSetting, setSavingSetting] = useState(false);

  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadsLoading, setLeadsLoading] = useState(false);
  const [leadsLoaded, setLeadsLoaded] = useState(false);

  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditLoaded, setAuditLoaded] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("nexus_admin_token");
    if (!token) {
      navigate("/admin/login");
      return;
    }
    api
      .get<Stats>("/admin/stats")
      .then((s) => {
        setStats(s);
        setLoading(false);
      })
      .catch(() => {
        localStorage.removeItem("nexus_admin_token");
        navigate("/admin/login");
      });
  }, [navigate]);

  function handleLogout() {
    localStorage.removeItem("nexus_admin_token");
    navigate("/admin/login");
  }

  async function loadQuestions() {
    if (questionsLoaded || questionsLoading) return;
    setQuestionsLoading(true);
    try {
      const data = await api.get<{ questions: AdminQuestion[] }>("/admin/questions");
      setQuestions(data.questions);
      setQuestionsLoaded(true);
    } finally {
      setQuestionsLoading(false);
    }
  }

  async function loadSettings() {
    if (settingsLoaded || settingsLoading) return;
    setSettingsLoading(true);
    try {
      const data = await api.get<{ settings: Setting[] }>("/admin/settings");
      setSettings(data.settings);
      setSettingsLoaded(true);
    } finally {
      setSettingsLoading(false);
    }
  }

  async function loadLeads() {
    if (leadsLoaded || leadsLoading) return;
    setLeadsLoading(true);
    try {
      const data = await api.get<{ leads: Lead[] }>("/admin/leads");
      setLeads(data.leads);
      setLeadsLoaded(true);
    } finally {
      setLeadsLoading(false);
    }
  }

  async function loadAudit() {
    if (auditLoaded || auditLoading) return;
    setAuditLoading(true);
    try {
      const data = await api.get<{ audit_logs: AuditEntry[] }>("/admin/audit-logs");
      setAuditLogs(data.audit_logs);
      setAuditLoaded(true);
    } finally {
      setAuditLoading(false);
    }
  }

  function switchTab(tab: Tab) {
    setActiveTab(tab);
    if (tab === "questions") loadQuestions();
    if (tab === "settings") loadSettings();
    if (tab === "leads") loadLeads();
    if (tab === "audit") loadAudit();
  }

  function openEditQuestion(q: AdminQuestion) {
    setEditingQuestion(q);
    setEditLabel(q.label);
    setEditWeight(String(q.weight));
    setEditHelpText(q.help_text ?? "");
  }

  async function saveQuestion() {
    if (!editingQuestion) return;
    setSavingQuestion(true);
    try {
      await api.put(`/admin/questions/${editingQuestion.id}`, {
        label: editLabel,
        weight: parseInt(editWeight, 10),
        help_text: editHelpText || null,
      });
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === editingQuestion.id
            ? { ...q, label: editLabel, weight: parseInt(editWeight, 10), help_text: editHelpText || null }
            : q
        )
      );
      setEditingQuestion(null);
    } finally {
      setSavingQuestion(false);
    }
  }

  async function toggleQuestion(id: number) {
    try {
      const result = await api.patch<{ id: number; is_active: boolean }>(
        `/admin/questions/${id}/toggle`
      );
      setQuestions((prev) =>
        prev.map((q) => (q.id === id ? { ...q, is_active: result.is_active } : q))
      );
    } catch {
      // silent
    }
  }

  function openEditSetting(s: Setting) {
    setEditingSetting(s);
    setEditSettingValue(JSON.stringify(s.value));
  }

  async function saveSetting() {
    if (!editingSetting) return;
    setSavingSetting(true);
    try {
      const parsed = JSON.parse(editSettingValue);
      await api.put(`/admin/settings/${editingSetting.key}`, { value: parsed });
      setSettings((prev) =>
        prev.map((s) => (s.key === editingSetting.key ? { ...s, value: parsed } : s))
      );
      setEditingSetting(null);
    } catch {
      // invalid JSON — modal stays open
    } finally {
      setSavingSetting(false);
    }
  }

  function exportLeadsCsv() {
    const header = "email,secteur,taille,date\n";
    const rows = leads
      .map(
        (l) =>
          `${l.contact_email},${l.sector ?? ""},${l.company_size ?? ""},${l.started_at ?? ""}`
      )
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads_nexus.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-clay" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line bg-white sticky top-0 z-30">
        <div className="container flex items-center justify-between h-[72px]">
          <div className="flex items-center gap-3">
            <Link to="/"><img src="/openlab.png" alt="OpenLab" className="h-11 sm:h-13 w-auto" /></Link>
            <span className="inline-flex items-center px-2.5 py-1 rounded-full font-mono text-[9px] uppercase tracking-[0.15em] font-bold hidden sm:flex"
                  style={{ background: "#FFF0E6", color: "#FF5500" }}>
              Admin
            </span>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="btn-ghost text-[13px]"
          >
            <LogOut size={14} />
            <span className="hidden sm:inline">Déconnexion</span>
          </button>
        </div>
      </header>

      <nav className="border-b border-line bg-bone-card" aria-label="Admin navigation">
        <div className="container flex gap-0.5 py-2 overflow-x-auto scrollbar-none">
          {(Object.keys(TAB_LABELS) as Tab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => switchTab(tab)}
              data-active={activeTab === tab}
              className="px-3 sm:px-4 py-2.5 font-mono text-[10px] uppercase tracking-[0.15em] rounded-lg
                         text-ink-mute hover:text-ink whitespace-nowrap transition-all duration-150
                         data-[active=true]:bg-white data-[active=true]:text-ink data-[active=true]:shadow-sm"
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </div>
      </nav>

      <main className="container py-12 flex-1">
        {activeTab === "dashboard" && (
          <section aria-label="Tableau de bord">
            <span className="pill pill-clay mb-6">Tableau de bord</span>
            <h1 className="font-serif font-light text-[clamp(2rem,5vw,3.5rem)] leading-[1.05] tracking-tight">
              Dashboard.
            </h1>
            {stats && (
              <div className="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-4">
                <KPI label="Sessions totales" value={String(stats.total_sessions)} />
                <KPI label="Finalisées" value={String(stats.completed_sessions)} />
                <KPI label="Taux de complétion" value={`${stats.completion_rate}%`} />
                <KPI
                  label="Score moyen"
                  value={
                    stats.average_global_score != null
                      ? `${stats.average_global_score}/100`
                      : "—"
                  }
                />
              </div>
            )}
          </section>
        )}

        {activeTab === "questions" && (
          <section aria-label="Gestion des questions">
            <h2 className="font-serif font-light text-[2rem] tracking-tight mb-8">
              Questions
            </h2>
            {questionsLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="animate-spin text-clay" size={24} />
              </div>
            ) : (
              <div className="space-y-px bg-line">
                {questions.map((q) => (
                  <div
                    key={q.id}
                    className="bg-bone-card p-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-mono text-[10px] text-clay">{q.code}</span>
                        <span
                          className={`font-mono text-[9px] px-1.5 py-0.5 rounded ${
                            q.is_active
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-600"
                          }`}
                        >
                          {q.is_active ? "Actif" : "Inactif"}
                        </span>
                        <span className="font-mono text-[9px] text-ink-mute">
                          Poids: {q.weight}
                        </span>
                      </div>
                      <p className="text-[14px] text-ink">{q.label}</p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => openEditQuestion(q)}
                        className="btn-ghost text-[11px]"
                        aria-label={`Modifier ${q.code}`}
                      >
                        Modifier
                      </button>
                      <button
                        type="button"
                        onClick={() => toggleQuestion(q.id)}
                        className="btn-ghost text-[11px]"
                        aria-label={`${q.is_active ? "Désactiver" : "Activer"} ${q.code}`}
                      >
                        {q.is_active ? "Désactiver" : "Activer"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {editingQuestion && (
              <div
                role="dialog"
                aria-modal="true"
                aria-label="Modifier la question"
                className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-6"
              >
                <div className="bg-bone-card w-full max-w-lg p-8 rounded-sm space-y-6">
                  <h3 className="font-serif text-[1.25rem]">
                    Modifier {editingQuestion.code}
                  </h3>
                  <div>
                    <label
                      htmlFor="edit-label"
                      className="block font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-2"
                    >
                      Libellé
                    </label>
                    <textarea
                      id="edit-label"
                      value={editLabel}
                      onChange={(e) => setEditLabel(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 bg-transparent border border-line rounded text-[14px]
                                 focus:outline-none focus:border-ink"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="edit-weight"
                      className="block font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-2"
                    >
                      Poids (1–20)
                    </label>
                    <input
                      id="edit-weight"
                      type="number"
                      min={1}
                      max={20}
                      value={editWeight}
                      onChange={(e) => setEditWeight(e.target.value)}
                      className="w-full px-3 py-2 bg-transparent border border-line rounded text-[14px]
                                 focus:outline-none focus:border-ink"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="edit-help"
                      className="block font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-2"
                    >
                      Texte d'aide (optionnel)
                    </label>
                    <textarea
                      id="edit-help"
                      value={editHelpText}
                      onChange={(e) => setEditHelpText(e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 bg-transparent border border-line rounded text-[14px]
                                 focus:outline-none focus:border-ink"
                    />
                  </div>
                  <div className="flex gap-3 justify-end">
                    <button
                      type="button"
                      onClick={() => setEditingQuestion(null)}
                      className="btn-ghost text-[13px]"
                    >
                      Annuler
                    </button>
                    <button
                      type="button"
                      onClick={saveQuestion}
                      disabled={savingQuestion || !editLabel.trim()}
                      className="btn-clay text-[13px] disabled:opacity-50"
                    >
                      {savingQuestion ? "Enregistrement…" : "Enregistrer"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === "settings" && (
          <section aria-label="Paramètres fiscaux">
            <h2 className="font-serif font-light text-[2rem] tracking-tight mb-8">
              Paramètres fiscaux
            </h2>
            {settingsLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="animate-spin text-clay" size={24} />
              </div>
            ) : (
              <div className="space-y-px bg-line">
                {settings.map((s) => (
                  <div
                    key={s.key}
                    className="bg-bone-card p-4 flex items-start justify-between gap-4"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-[10px] text-clay mb-1">{s.key}</div>
                      {s.description && (
                        <p className="text-[12px] text-ink-mute mb-1">{s.description}</p>
                      )}
                      <code className="text-[13px] text-ink">
                        {JSON.stringify(s.value)}
                      </code>
                    </div>
                    <button
                      type="button"
                      onClick={() => openEditSetting(s)}
                      className="btn-ghost text-[11px] shrink-0"
                      aria-label={`Modifier ${s.key}`}
                    >
                      Modifier
                    </button>
                  </div>
                ))}
              </div>
            )}

            {editingSetting && (
              <div
                role="dialog"
                aria-modal="true"
                aria-label="Modifier le paramètre"
                className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-6"
              >
                <div className="bg-bone-card w-full max-w-lg p-8 rounded-sm space-y-6">
                  <h3 className="font-serif text-[1.25rem]">
                    Modifier {editingSetting.key}
                  </h3>
                  <div>
                    <label
                      htmlFor="edit-setting-value"
                      className="block font-mono text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-2"
                    >
                      Valeur (JSON)
                    </label>
                    <textarea
                      id="edit-setting-value"
                      value={editSettingValue}
                      onChange={(e) => setEditSettingValue(e.target.value)}
                      rows={4}
                      className="w-full px-3 py-2 bg-transparent border border-line rounded
                                 font-mono text-[13px] focus:outline-none focus:border-ink"
                    />
                  </div>
                  <div className="flex gap-3 justify-end">
                    <button
                      type="button"
                      onClick={() => setEditingSetting(null)}
                      className="btn-ghost text-[13px]"
                    >
                      Annuler
                    </button>
                    <button
                      type="button"
                      onClick={saveSetting}
                      disabled={savingSetting}
                      className="btn-clay text-[13px] disabled:opacity-50"
                    >
                      {savingSetting ? "Enregistrement…" : "Enregistrer"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === "leads" && (
          <section aria-label="Leads opt-in">
            <div className="flex items-center justify-between mb-8">
              <h2 className="font-serif font-light text-[2rem] tracking-tight">Leads</h2>
              {leads.length > 0 && (
                <button
                  type="button"
                  onClick={exportLeadsCsv}
                  className="btn-clay text-[13px]"
                  aria-label="Exporter CSV"
                >
                  Exporter CSV
                </button>
              )}
            </div>
            {leadsLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="animate-spin text-clay" size={24} />
              </div>
            ) : leads.length === 0 ? (
              <p className="text-[14px] text-ink-mute">Aucun lead opt-in pour le moment.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead>
                    <tr className="border-b border-line font-mono text-[10px] uppercase tracking-[0.15em] text-ink-mute">
                      <th className="text-left py-3 pr-6">Email</th>
                      <th className="text-left py-3 pr-6">Secteur</th>
                      <th className="text-left py-3 pr-6">Taille</th>
                      <th className="text-left py-3">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map((l) => (
                      <tr key={l.session_id} className="border-b border-line">
                        <td className="py-3 pr-6">{l.contact_email}</td>
                        <td className="py-3 pr-6">{l.sector ?? "—"}</td>
                        <td className="py-3 pr-6">{l.company_size ?? "—"}</td>
                        <td className="py-3 text-ink-mute">
                          {l.started_at
                            ? new Date(l.started_at).toLocaleDateString("fr-CI")
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {activeTab === "audit" && (
          <section aria-label="Journal d'audit">
            <h2 className="font-serif font-light text-[2rem] tracking-tight mb-8">
              Journal d'audit
            </h2>
            {auditLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="animate-spin text-clay" size={24} />
              </div>
            ) : auditLogs.length === 0 ? (
              <p className="text-[14px] text-ink-mute">Aucune entrée d'audit.</p>
            ) : (
              <div className="space-y-px bg-line">
                {auditLogs.map((log) => (
                  <div
                    key={log.id}
                    className="bg-bone-card p-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-[12px]"
                  >
                    <div>
                      <div className="font-mono text-[9px] text-ink-mute mb-1">Action</div>
                      <div className="font-medium">{log.action}</div>
                    </div>
                    <div>
                      <div className="font-mono text-[9px] text-ink-mute mb-1">Acteur</div>
                      <div>
                        {log.actor_type}
                        {log.actor_id ? ` · ${log.actor_id}` : ""}
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[9px] text-ink-mute mb-1">Ressource</div>
                      <div>
                        {log.resource_type ?? "—"}
                        {log.resource_id ? ` · ${log.resource_id}` : ""}
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[9px] text-ink-mute mb-1">Date</div>
                      <div className="text-ink-mute">
                        {log.created_at
                          ? new Date(log.created_at).toLocaleString("fr-CI")
                          : "—"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

function KPI({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border border-line rounded-xl p-6 sm:p-8 hover:border-[#FF5500]/30 transition-colors duration-200">
      <div className="font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.2em] text-ink-mute mb-3">
        {label}
      </div>
      <div className="tabular text-[28px] sm:text-[36px] font-black text-ink leading-none"
           style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        {value}
      </div>
    </div>
  );
}
