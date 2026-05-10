import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, ApiClientError } from "@/lib/api";

describe("api client", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("GET — retourne le JSON parsé en cas de succès", async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    const result = await api.get<{ ok: boolean }>("/test");
    expect(result.ok).toBe(true);
  });

  it("POST — sérialise le body en JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 1 }), { status: 201 })
    );
    global.fetch = fetchMock;
    await api.post("/items", { name: "abc" });
    const init = fetchMock.mock.calls[0]![1] as RequestInit;
    expect(init.body).toBe(JSON.stringify({ name: "abc" }));
    expect(init.method).toBe("POST");
  });

  it("injecte le JWT s'il est présent dans le localStorage", async () => {
    localStorage.setItem("nexus_admin_token", "jwt.token.here");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("{}", { status: 200 })
    );
    global.fetch = fetchMock;
    await api.get("/admin/stats");
    const init = fetchMock.mock.calls[0]![1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer jwt.token.here");
  });

  it("convertit une erreur RFC 7807 en ApiClientError", async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          type: "not_found",
          title: "Ressource introuvable",
          status: 404,
          detail: "La session n'existe pas",
        }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      )
    );
    await expect(api.get("/sessions/x")).rejects.toBeInstanceOf(ApiClientError);
  });

  it("gère un 204 No Content", async () => {
    global.fetch = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    const result = await api.delete<undefined>("/sessions/x");
    expect(result).toBeUndefined();
  });

  it("normalise une erreur réseau non-JSON", async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response("Internal Error", {
        status: 500,
        statusText: "Internal Server Error",
      })
    );
    try {
      await api.get("/x");
      expect.fail("Devait lever une erreur");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiClientError);
      expect((err as ApiClientError).status).toBe(500);
    }
  });

  it("expose les méthodes PUT et PATCH", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(() => Promise.resolve(new Response("{}", { status: 200 })));
    global.fetch = fetchMock;
    await api.put("/x", { a: 1 });
    expect((fetchMock.mock.calls[0]![1] as RequestInit).method).toBe("PUT");
    await api.patch("/x", { a: 1 });
    expect((fetchMock.mock.calls[1]![1] as RequestInit).method).toBe("PATCH");
  });
});
