import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DiagnosticStart } from "@/pages/DiagnosticStart";
import { Generating } from "@/pages/Generating";
import { ReportView } from "@/pages/ReportView";
import { Questionnaire } from "@/pages/Questionnaire";
import { Landing } from "@/pages/Landing";
import { AdminLogin } from "@/pages/AdminLogin";
import { AdminDashboard } from "@/pages/AdminDashboard";
import { NotFound } from "@/pages/NotFound";

// Mock the api module
vi.mock("@/lib/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
  ApiClientError: class ApiClientError extends Error {
    status: number;
    type: string;
    detail: string;
    constructor(error: { type: string; title: string; status: number; detail: string }) {
      super(error.detail || error.title);
      this.name = "ApiClientError";
      this.status = error.status;
      this.type = error.type;
      this.detail = error.detail;
    }
  },
}));

import { api } from "@/lib/api";
const mockApi = api as { get: ReturnType<typeof vi.fn>; post: ReturnType<typeof vi.fn> };

function renderInRouter(
  element: React.ReactElement,
  path = "/",
  initialEntry = "/"
) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path={path} element={element} />
      </Routes>
    </MemoryRouter>
  );
}

// ---------------------------------------------------------------------------
// Landing
// ---------------------------------------------------------------------------
describe("Landing", () => {
  it("affiche la headline principale", () => {
    renderInRouter(<Landing />, "/", "/");
    expect(screen.getByText(/Commencer le diagnostic/i)).toBeTruthy();
  });

  it("affiche la mention ARTCI dans le footer", () => {
    renderInRouter(<Landing />, "/", "/");
    expect(screen.getByText(/2013-450/i)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// NotFound
// ---------------------------------------------------------------------------
describe("NotFound", () => {
  it("affiche le message 404", () => {
    renderInRouter(<NotFound />, "*", "/inexistant");
    expect(screen.getByText(/404/i)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// DiagnosticStart
// ---------------------------------------------------------------------------
describe("DiagnosticStart", () => {
  beforeEach(() => vi.clearAllMocks());

  it("rend les sélecteurs de taille et secteur", () => {
    renderInRouter(<DiagnosticStart />, "/diagnostic/start", "/diagnostic/start");
    expect(screen.getByText("1 — 10")).toBeTruthy();
    expect(screen.getByText("Banque & Assurance")).toBeTruthy();
  });

  it("bouton CTA désactivé si taille ou secteur non sélectionné", () => {
    renderInRouter(<DiagnosticStart />, "/diagnostic/start", "/diagnostic/start");
    const btn = screen.getByRole("button", { name: /Lancer le diagnostic/i });
    expect(btn).toHaveProperty("disabled", true);
  });

  it("active CTA après sélection taille + secteur", async () => {
    renderInRouter(<DiagnosticStart />, "/diagnostic/start", "/diagnostic/start");
    const sizeBtn = screen.getByText("51 — 200");
    const sectorBtn = screen.getByText("BTP & Immobilier");
    fireEvent.click(sizeBtn);
    fireEvent.click(sectorBtn);
    const cta = screen.getByRole("button", { name: /Lancer le diagnostic/i });
    expect(cta).toHaveProperty("disabled", false);
  });

  it("appelle POST /sessions et navigue sur succès", async () => {
    mockApi.post.mockResolvedValue({ session_id: "sess-abc123" });
    render(
      <MemoryRouter initialEntries={["/diagnostic/start"]}>
        <Routes>
          <Route path="/diagnostic/start" element={<DiagnosticStart />} />
          <Route
            path="/diagnostic/:sessionId/q/1"
            element={<div data-testid="questionnaire" />}
          />
        </Routes>
      </MemoryRouter>
    );
    fireEvent.click(screen.getByText("51 — 200"));
    fireEvent.click(screen.getByText("Services & Conseil"));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Lancer le diagnostic/i }));
    });
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith(
        "/sessions",
        expect.objectContaining({ company_size: "51-200" })
      );
    });
  });

  it("affiche l'erreur API en cas d'échec", async () => {
    const { ApiClientError } = await import("@/lib/api");
    mockApi.post.mockRejectedValue(
      new ApiClientError({ type: "error", title: "Erreur", status: 500, detail: "Erreur serveur" })
    );
    renderInRouter(<DiagnosticStart />, "/diagnostic/start", "/diagnostic/start");
    fireEvent.click(screen.getByText("51 — 200"));
    fireEvent.click(screen.getByText("Services & Conseil"));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Lancer le diagnostic/i }));
    });
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// Questionnaire
// ---------------------------------------------------------------------------
describe("Questionnaire", () => {
  beforeEach(() => vi.clearAllMocks());

  const MOCK_QUESTIONS = [
    { id: 1, code: "Q01", category: "FISCALE", answer_type: "YES_NO_PARTIAL", label: "Question 1 ?", help_text: null },
    { id: 2, code: "Q02", category: "SOCIALE", answer_type: "YES_NO", label: "Question 2 ?", help_text: "Aide Q2" },
  ];

  it("affiche un loader pendant le chargement", () => {
    mockApi.get.mockReturnValue(new Promise(() => {})); // never resolves
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
        </Routes>
      </MemoryRouter>
    );
    expect(document.querySelector(".animate-spin")).toBeTruthy();
  });

  it("affiche la question chargée", async () => {
    mockApi.get.mockResolvedValue({ questions: MOCK_QUESTIONS });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Question 1 ?")).toBeTruthy();
    });
  });

  it("affiche les options YES/PARTIAL/NO pour YES_NO_PARTIAL", async () => {
    mockApi.get.mockResolvedValue({ questions: MOCK_QUESTIONS });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("Question 1 ?"));
    expect(screen.getByText("Oui")).toBeTruthy();
    expect(screen.getByText("Partiellement")).toBeTruthy();
    expect(screen.getByText("Non")).toBeTruthy();
  });

  it("appelle POST /responses au clic sur une option", async () => {
    mockApi.get.mockResolvedValue({ questions: MOCK_QUESTIONS });
    mockApi.post.mockResolvedValue({ saved: true, progress: { answered: 1, total: 2, percent: 50 } });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<div />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("Oui"));
    fireEvent.click(screen.getByText("Oui"));
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith(
        "/sessions/sess1/responses",
        expect.objectContaining({ answer_value: "YES" })
      );
    });
  });

  it("affiche 'Question introuvable' quand l'index dépasse les questions", async () => {
    mockApi.get.mockResolvedValue({ questions: MOCK_QUESTIONS });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/q/99"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText(/Question introuvable/i)).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// Generating
// ---------------------------------------------------------------------------
describe("Generating", () => {
  beforeEach(() => vi.clearAllMocks());

  it("appelle POST /finalize au montage", async () => {
    mockApi.post.mockResolvedValue({ report_id: "rpt-1", status: "GENERATING" });
    mockApi.get.mockResolvedValue({ status: "GENERATING" });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/generating"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/generating" element={<Generating />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(
      () => expect(mockApi.post).toHaveBeenCalledWith("/sessions/sess1/finalize"),
      { timeout: 3000 }
    );
  });

  it("affiche l'erreur si la finalisation échoue", async () => {
    const { ApiClientError } = await import("@/lib/api");
    mockApi.post.mockRejectedValue(
      new ApiClientError({ type: "error", title: "Err", status: 422, detail: "Finalisation impossible" })
    );
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/generating"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/generating" element={<Generating />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(
      () => expect(screen.getByRole("alert")).toBeTruthy(),
      { timeout: 3000 }
    );
  });

  it("navigue vers le rapport quand status=READY", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockApi.post.mockResolvedValue({ report_id: "rpt-1", status: "GENERATING" });
    mockApi.get.mockResolvedValue({ status: "READY" });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sess1/generating"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/generating" element={<Generating />} />
          <Route path="/diagnostic/report/:reportId" element={<div data-testid="report" />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => expect(mockApi.post).toHaveBeenCalled(), { timeout: 3000 });
    await act(async () => {
      vi.advanceTimersByTime(2500);
    });
    await waitFor(
      () => expect(screen.queryByTestId("report")).toBeTruthy(),
      { timeout: 3000 }
    );
    vi.useRealTimers();
  });
});

// ---------------------------------------------------------------------------
// ReportView
// ---------------------------------------------------------------------------
describe("ReportView", () => {
  beforeEach(() => vi.clearAllMocks());

  const MOCK_REPORT = {
    report_id: "rpt-abc",
    status: "READY",
    global_score: 47.5,
    maturity_level: "EMERGENT",
    scores_by_category: { FISCALE: 60, SOCIALE: 40, CONFORMITE: 50, DIGITALE: 35 },
    risk_score: 72.3,
    financial_exposure_fcfa: 18_500_000,
    digital_gap_pct: 65,
    executive_summary: "Votre organisation est en risque élevé.",
    risks_detected: [
      { id: "R-FISC-01", title: "IGR non conforme", severity: "HIGH", fcfa_impact: 1_200_000 },
    ],
    recommendations: [
      {
        priority: 1, title: "IGR 2024", description: "Mise à jour paie.",
        expected_gain_fcfa: 500_000, implementation_weeks: 4, nexusrh_module: "NexusRH Paie",
      },
    ],
    pdf_url: "https://api.nexusrh.ci/reports/rpt-abc/pdf?token=xxx",
  };

  it("affiche un loader pendant le chargement", () => {
    mockApi.get.mockReturnValue(new Promise(() => {}));
    render(
      <MemoryRouter initialEntries={["/diagnostic/report/rpt-abc"]}>
        <Routes>
          <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
        </Routes>
      </MemoryRouter>
    );
    expect(document.querySelector(".animate-spin")).toBeTruthy();
  });

  it("affiche le score global", async () => {
    mockApi.get.mockResolvedValue(MOCK_REPORT);
    render(
      <MemoryRouter initialEntries={["/diagnostic/report/rpt-abc"]}>
        <Routes>
          <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("48")).toBeTruthy(); // Math.round(47.5)
    });
  });

  it("affiche les risques détectés", async () => {
    mockApi.get.mockResolvedValue(MOCK_REPORT);
    render(
      <MemoryRouter initialEntries={["/diagnostic/report/rpt-abc"]}>
        <Routes>
          <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("IGR non conforme")).toBeTruthy();
    });
  });

  it("affiche les recommandations", async () => {
    mockApi.get.mockResolvedValue(MOCK_REPORT);
    render(
      <MemoryRouter initialEntries={["/diagnostic/report/rpt-abc"]}>
        <Routes>
          <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("IGR 2024")).toBeTruthy();
    });
  });

  it("affiche un lien PDF si pdf_url est défini", async () => {
    mockApi.get.mockResolvedValue(MOCK_REPORT);
    render(
      <MemoryRouter initialEntries={["/diagnostic/report/rpt-abc"]}>
        <Routes>
          <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText(/Télécharger le PDF/i)).toBeTruthy();
    });
  });

  it("affiche l'erreur si le rapport est introuvable", async () => {
    mockApi.get.mockRejectedValue({ detail: "Rapport introuvable." });
    render(
      <MemoryRouter initialEntries={["/diagnostic/report/rpt-abc"]}>
        <Routes>
          <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
  });

  it("appelle POST /send au clic sur 'Recevoir par email'", async () => {
    mockApi.get.mockResolvedValue(MOCK_REPORT);
    mockApi.post.mockResolvedValue({ sent: true });
    render(
      <MemoryRouter initialEntries={["/diagnostic/report/rpt-abc"]}>
        <Routes>
          <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText(/Recevoir par email/i));
    fireEvent.click(screen.getByText(/Recevoir par email/i));
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith("/reports/rpt-abc/send");
    });
  });
});

// ---------------------------------------------------------------------------
// Questionnaire — branches supplémentaires
// ---------------------------------------------------------------------------
describe("Questionnaire — branches supplémentaires", () => {
  beforeEach(() => vi.clearAllMocks());

  const NUMERIC_QUESTION = [
    { id: 8, code: "Q08", category: "DIGITALE", answer_type: "FREE_NUMERIC", label: "Heures perdues ?", help_text: "Aidez-nous." },
  ];

  it("affiche NumericInput pour FREE_NUMERIC et valide sur Entrée", async () => {
    mockApi.get.mockResolvedValue({ questions: NUMERIC_QUESTION });
    mockApi.post.mockResolvedValue({ saved: true, progress: { answered: 1, total: 1, percent: 100 } });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sessN/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
          <Route path="/diagnostic/:sessionId/generating" element={<div data-testid="generating" />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("Heures perdues ?"));
    const input = screen.getByRole("spinbutton");
    fireEvent.change(input, { target: { value: "5" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(mockApi.post).toHaveBeenCalled());
  });

  it("affiche le texte d'aide quand help_text est défini", async () => {
    mockApi.get.mockResolvedValue({ questions: NUMERIC_QUESTION });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sessN/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("Heures perdues ?"));
    expect(screen.getByText(/comprendre cette question/i)).toBeTruthy();
  });

  it("bouton Précédent désactivé à la première question", async () => {
    mockApi.get.mockResolvedValue({ questions: [
      { id: 1, code: "Q01", category: "FISCALE", answer_type: "YES_NO", label: "Q1?", help_text: null },
      { id: 2, code: "Q02", category: "SOCIALE", answer_type: "YES_NO", label: "Q2?", help_text: null },
    ]});
    render(
      <MemoryRouter initialEntries={["/diagnostic/sessN/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("Q1?"));
    const prevBtn = screen.getByRole("button", { name: /précédent/i });
    expect(prevBtn).toHaveProperty("disabled", true);
  });

  it("raccourci clavier 1 sélectionne YES et avance", async () => {
    mockApi.get.mockResolvedValue({ questions: [
      { id: 1, code: "Q01", category: "FISCALE", answer_type: "YES_NO", label: "Q1?", help_text: null },
      { id: 2, code: "Q02", category: "SOCIALE", answer_type: "YES_NO", label: "Q2?", help_text: null },
    ]});
    mockApi.post.mockResolvedValue({ saved: true, progress: { answered: 1, total: 2, percent: 50 } });
    render(
      <MemoryRouter initialEntries={["/diagnostic/sessN/q/1"]}>
        <Routes>
          <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("Q1?"));
    fireEvent.keyDown(document.body, { key: "1" });
    await waitFor(() => expect(mockApi.post).toHaveBeenCalledWith(
      "/sessions/sessN/responses",
      expect.objectContaining({ answer_value: "YES" })
    ));
  });
});

// ---------------------------------------------------------------------------
// AdminLogin
// ---------------------------------------------------------------------------
describe("AdminLogin", () => {
  beforeEach(() => vi.clearAllMocks());

  it("affiche le formulaire de connexion", () => {
    renderInRouter(<AdminLogin />, "/admin/login", "/admin/login");
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
  });

  it("affiche l'erreur si login échoue", async () => {
    const { ApiClientError } = await import("@/lib/api");
    mockApi.post.mockRejectedValue(
      new ApiClientError({ type: "unauthorized", title: "Erreur", status: 401, detail: "Identifiants incorrects." })
    );
    renderInRouter(<AdminLogin />, "/admin/login", "/admin/login");
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "bad@test.ci" } });
    fireEvent.change(screen.getByLabelText(/mot de passe/i), { target: { value: "WrongPass123!" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /se connecter/i }));
    });
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  });

  it("appelle POST /auth/login au submit", async () => {
    mockApi.post.mockResolvedValue({ access_token: "jwt.tok", token_type: "bearer", expires_in: 28800 });
    render(
      <MemoryRouter initialEntries={["/admin/login"]}>
        <Routes>
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<div data-testid="dashboard" />} />
        </Routes>
      </MemoryRouter>
    );
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "admin@test.ci" },
    });
    fireEvent.change(screen.getByLabelText(/mot de passe/i), {
      target: { value: "AdminPass123!" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /se connecter/i }));
    });
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith(
        "/auth/login",
        expect.objectContaining({ email: "admin@test.ci" })
      );
    });
  });
});

// ---------------------------------------------------------------------------
// AdminDashboard
// ---------------------------------------------------------------------------
describe("AdminDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("redirige vers /admin/login si pas de token", async () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId("login-redirect")).toBeTruthy();
    });
  });

  it("affiche les KPIs quand le token est valide", async () => {
    localStorage.setItem("nexus_admin_token", "jwt.valid");
    mockApi.get.mockResolvedValue({
      total_sessions: 42,
      completed_sessions: 30,
      completion_rate: 71.4,
      average_global_score: 55.3,
    });
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("42")).toBeTruthy();
    });
  });

  it("redirige si l'API renvoie une erreur auth", async () => {
    localStorage.setItem("nexus_admin_token", "jwt.expired");
    mockApi.get.mockRejectedValue({ status: 401, detail: "Token expiré" });
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId("login-redirect")).toBeTruthy();
    });
  });

  it("bouton déconnexion efface le token et redirige", async () => {
    localStorage.setItem("nexus_admin_token", "jwt.valid");
    mockApi.get.mockResolvedValue({
      total_sessions: 10, completed_sessions: 5, completion_rate: 50, average_global_score: null,
    });
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => screen.getByRole("button", { name: /déconnexion/i }));
    fireEvent.click(screen.getByRole("button", { name: /déconnexion/i }));
    await waitFor(() => {
      expect(localStorage.getItem("nexus_admin_token")).toBeNull();
      expect(screen.getByTestId("login-redirect")).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// AdminDashboard — onglet Questions
// ---------------------------------------------------------------------------
describe("AdminDashboard — Questions tab", () => {
  const STATS = { total_sessions: 3, completed_sessions: 2, completion_rate: 66.7, average_global_score: null };
  const QUESTIONS = [
    { id: 1, code: "Q01", label: "Vos bulletins ?", category: "FISCALE", weight: 10,
      answer_type: "YES_NO_PARTIAL", order: 1, is_active: true, help_text: null },
  ];

  function renderAdmin() {
    return render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("nexus_admin_token", "jwt.valid");
  });

  it("affiche les questions après clic sur l'onglet", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ questions: QUESTIONS });
    renderAdmin();
    await waitFor(() => screen.getByText("3"));
    fireEvent.click(screen.getByText("Questions"));
    await waitFor(() => expect(screen.getByText("Vos bulletins ?")).toBeTruthy());
  });

  it("ouvre la modale d'édition au clic sur Modifier", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ questions: QUESTIONS });
    renderAdmin();
    await waitFor(() => screen.getByText("3"));
    fireEvent.click(screen.getByText("Questions"));
    await waitFor(() => screen.getByText("Vos bulletins ?"));
    fireEvent.click(screen.getByLabelText("Modifier Q01"));
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("appelle PUT /admin/questions/{id} lors de l'enregistrement", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ questions: QUESTIONS });
    (api.put as ReturnType<typeof vi.fn>).mockResolvedValue({ updated: true, id: 1 });
    renderAdmin();
    await waitFor(() => screen.getByText("3"));
    fireEvent.click(screen.getByText("Questions"));
    await waitFor(() => screen.getByText("Vos bulletins ?"));
    fireEvent.click(screen.getByLabelText("Modifier Q01"));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /enregistrer/i }));
    });
    await waitFor(() =>
      expect(api.put as ReturnType<typeof vi.fn>).toHaveBeenCalledWith(
        "/admin/questions/1",
        expect.objectContaining({ label: "Vos bulletins ?" })
      )
    );
  });

  it("appelle PATCH /admin/questions/{id}/toggle sur le bouton toggle", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ questions: QUESTIONS });
    (api.patch as ReturnType<typeof vi.fn>).mockResolvedValue({ id: 1, is_active: false });
    renderAdmin();
    await waitFor(() => screen.getByText("3"));
    fireEvent.click(screen.getByText("Questions"));
    await waitFor(() => screen.getByLabelText("Désactiver Q01"));
    fireEvent.click(screen.getByLabelText("Désactiver Q01"));
    await waitFor(() =>
      expect(api.patch as ReturnType<typeof vi.fn>).toHaveBeenCalledWith(
        "/admin/questions/1/toggle"
      )
    );
  });
});

// ---------------------------------------------------------------------------
// AdminDashboard — onglet Paramètres
// ---------------------------------------------------------------------------
describe("AdminDashboard — Settings tab", () => {
  const STATS = { total_sessions: 77, completed_sessions: 0, completion_rate: 0, average_global_score: null };
  const SETTINGS = [
    { key: "cnps_employer_rate", value: 0.105, description: "Taux patronal CNPS" },
  ];

  function renderAdmin() {
    return render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("nexus_admin_token", "jwt.valid");
  });

  it("affiche les paramètres après clic sur l'onglet", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ settings: SETTINGS });
    renderAdmin();
    await waitFor(() => screen.getByText("77"));
    fireEvent.click(screen.getByText("Paramètres"));
    await waitFor(() => expect(screen.getByText("cnps_employer_rate")).toBeTruthy());
  });

  it("appelle PUT /admin/settings/{key} lors de l'enregistrement", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ settings: SETTINGS });
    (api.put as ReturnType<typeof vi.fn>).mockResolvedValue({ updated: true, key: "cnps_employer_rate" });
    renderAdmin();
    await waitFor(() => screen.getByText("77"));
    fireEvent.click(screen.getByText("Paramètres"));
    await waitFor(() => screen.getByText("cnps_employer_rate"));
    fireEvent.click(screen.getByLabelText("Modifier cnps_employer_rate"));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /enregistrer/i }));
    });
    await waitFor(() =>
      expect(api.put as ReturnType<typeof vi.fn>).toHaveBeenCalledWith(
        "/admin/settings/cnps_employer_rate",
        expect.objectContaining({ value: 0.105 })
      )
    );
  });
});

// ---------------------------------------------------------------------------
// AdminDashboard — onglet Leads
// ---------------------------------------------------------------------------
describe("AdminDashboard — Leads tab", () => {
  const STATS = { total_sessions: 88, completed_sessions: 80, completion_rate: 90, average_global_score: 55 };
  const LEADS = [
    { session_id: "s1", contact_email: "drh@example.ci", sector: "BTP", company_size: "51-200", started_at: "2026-05-01T10:00:00Z" },
  ];

  function renderAdmin() {
    return render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("nexus_admin_token", "jwt.valid");
  });

  it("affiche les leads dans le tableau", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ leads: LEADS });
    renderAdmin();
    await waitFor(() => screen.getByText("88"));
    fireEvent.click(screen.getByText("Leads"));
    await waitFor(() => expect(screen.getByText("drh@example.ci")).toBeTruthy());
  });

  it("affiche le bouton Exporter CSV quand il y a des leads", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ leads: LEADS });
    renderAdmin();
    await waitFor(() => screen.getByText("88"));
    fireEvent.click(screen.getByText("Leads"));
    await waitFor(() => expect(screen.getByLabelText("Exporter CSV")).toBeTruthy());
  });

  it("affiche le message vide sans leads", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ leads: [] });
    renderAdmin();
    await waitFor(() => screen.getByText("88"));
    fireEvent.click(screen.getByText("Leads"));
    await waitFor(() => expect(screen.getByText(/Aucun lead/i)).toBeTruthy());
  });
});

// ---------------------------------------------------------------------------
// AdminDashboard — onglet Audit
// ---------------------------------------------------------------------------
describe("AdminDashboard — Audit tab", () => {
  const STATS = { total_sessions: 99, completed_sessions: 0, completion_rate: 0, average_global_score: null };

  function renderAdmin() {
    return render(
      <MemoryRouter initialEntries={["/admin"]}>
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/login" element={<div data-testid="login-redirect" />} />
        </Routes>
      </MemoryRouter>
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("nexus_admin_token", "jwt.valid");
  });

  it("affiche 'Aucune entrée' quand le journal est vide", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ audit_logs: [] });
    renderAdmin();
    await waitFor(() => screen.getByText("99"));
    fireEvent.click(screen.getByText("Audit"));
    await waitFor(() => expect(screen.getByText(/Aucune entrée/i)).toBeTruthy());
  });

  it("affiche les entrées d'audit", async () => {
    mockApi.get
      .mockResolvedValueOnce(STATS)
      .mockResolvedValueOnce({ audit_logs: [
        { id: 1, actor_type: "ADMIN", actor_id: "1", action: "LOGIN",
          resource_type: null, resource_id: null, created_at: "2026-05-01T10:00:00Z" },
      ]});
    renderAdmin();
    await waitFor(() => screen.getByText("99"));
    fireEvent.click(screen.getByText("Audit"));
    await waitFor(() => expect(screen.getByText("LOGIN")).toBeTruthy());
  });
});
