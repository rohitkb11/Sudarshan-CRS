import React, { useState } from "react";
import { PipelineResult } from "./types";

export function App() {
  const [target, setTarget] = useState("example-target");
  const [mode, setMode] = useState<"full" | "delta">("full");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runScan = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/scans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, mode }),
      });
      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}: ${await response.text()}`);
      }
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to trigger scan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: "Inter, -apple-system, sans-serif", background: "#0a0e17", color: "#e2e8f0", minHeight: "100vh", padding: "2rem" }}>
      <header style={{ borderBottom: "1px solid #1e293b", paddingBottom: "1.5rem", marginBottom: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: "1.75rem", fontWeight: 700, color: "#38bdf8", letterSpacing: "-0.025em" }}>
              AI KAVACH — Autonomous Cyber-Reasoning System
            </h1>
            <p style={{ margin: "0.25rem 0 0", color: "#94a3b8", fontSize: "0.875rem" }}>
              Find the bug. Prove it's real. Fix it. Prove the fix holds. All without a human in the loop.
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <span style={{ background: "#0f172a", border: "1px solid #334155", padding: "0.4rem 0.8rem", borderRadius: "6px", fontSize: "0.8rem", color: "#38bdf8" }}>
              TCQ 2026
            </span>
            <span style={{ background: "#0f172a", border: "1px solid #334155", padding: "0.4rem 0.8rem", borderRadius: "6px", fontSize: "0.8rem", color: "#f97316" }}>
              ⚡ Groq LPU Powered
            </span>
            <span style={{ background: "#0f172a", border: "1px solid #334155", padding: "0.4rem 0.8rem", borderRadius: "6px", fontSize: "0.8rem", color: "#a855f7" }}>
              Buttercup v2
            </span>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: "1200px", margin: "0 auto" }}>
        {/* Controls */}
        <section style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "1.5rem", marginBottom: "2rem" }}>
          <h2 style={{ fontSize: "1.1rem", margin: "0 0 1rem", color: "#f1f5f9" }}>Autonomous Scan Control</h2>
          <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.3rem" }}>Target Repo</label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                style={{ background: "#1e293b", border: "1px solid #334155", color: "#f8fafc", padding: "0.5rem 0.8rem", borderRadius: "4px", fontSize: "0.9rem" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.3rem" }}>Scan Mode</label>
              <select
                value={mode}
                onChange={(e: any) => setMode(e.target.value)}
                style={{ background: "#1e293b", border: "1px solid #334155", color: "#f8fafc", padding: "0.5rem 0.8rem", borderRadius: "4px", fontSize: "0.9rem" }}
              >
                <option value="full">Full Codebase Scan</option>
                <option value="delta">Delta / PR Scan</option>
              </select>
            </div>
            <div style={{ alignSelf: "flex-end" }}>
              <button
                onClick={runScan}
                disabled={loading}
                style={{
                  background: loading ? "#475569" : "#0284c7",
                  color: "#ffffff",
                  border: "none",
                  padding: "0.55rem 1.4rem",
                  borderRadius: "4px",
                  fontWeight: 600,
                  cursor: loading ? "not-allowed" : "pointer",
                  transition: "background 0.2s",
                }}
              >
                {loading ? "Running CRS Pipeline..." : "Trigger Autonomous Scan"}
              </button>
            </div>
          </div>
          {error && <p style={{ color: "#ef4444", marginTop: "1rem", fontSize: "0.875rem" }}>Error: {error}</p>}
        </section>

        {/* Results */}
        {result && (
          <div>
            {/* Status Header */}
            <div
              style={{
                background: result.status === "verified" ? "#064e3b" : result.status === "unverified" ? "#78350f" : "#1e293b",
                border: `1px solid ${result.status === "verified" ? "#059669" : "#d97706"}`,
                borderRadius: "8px",
                padding: "1.25rem 1.5rem",
                marginBottom: "2rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <span style={{ textTransform: "uppercase", fontWeight: 700, fontSize: "0.8rem", letterSpacing: "0.05em", color: "#a7f3d0" }}>
                  Pipeline Status
                </span>
                <h3 style={{ margin: "0.2rem 0", fontSize: "1.5rem", color: "#ffffff" }}>
                  {result.status === "verified" ? "✅ FIX PROVEN & VERIFIED" : `⚠️ ${result.status.toUpperCase()}`}
                </h3>
                <p style={{ margin: 0, fontSize: "0.9rem", color: "#e2e8f0" }}>{result.message}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Attempts / Retry Cap</span>
                <div style={{ fontSize: "1.2rem", fontWeight: 700 }}>{result.attempts} / 3</div>
              </div>
            </div>

            {/* Proof Checklist Grid */}
            {result.verification && (
              <section style={{ marginBottom: "2rem" }}>
                <h2 style={{ fontSize: "1.2rem", marginBottom: "1rem", color: "#f8fafc" }}>
                  Evidence Proof Checklist (§8 Non-negotiable Acceptance Test)
                </h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}>
                  {[
                    { key: "clean_rebuild", label: "V1 Clean Rebuild", desc: "Patched code compiles without error" },
                    { key: "pov_replay", label: "V2 Original PoV Replay", desc: "Original crashing input no longer crashes" },
                    { key: "regression_suite", label: "V3 Regression Suite", desc: "Existing tests still pass in full" },
                    { key: "differential_refuzz", label: "V4 Differential Re-Fuzz", desc: "Mutated variants don't crash nearby" },
                  ].map((item) => {
                    const passed = (result.verification as any)[item.key];
                    return (
                      <div
                        key={item.key}
                        style={{
                          background: "#0f172a",
                          border: `1px solid ${passed ? "#10b981" : "#ef4444"}`,
                          borderRadius: "8px",
                          padding: "1rem",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{item.label}</span>
                          <span
                            style={{
                              background: passed ? "#064e3b" : "#7f1d1d",
                              color: passed ? "#6ee7b7" : "#fca5a5",
                              padding: "0.2rem 0.5rem",
                              borderRadius: "4px",
                              fontSize: "0.75rem",
                              fontWeight: 700,
                            }}
                          >
                            {passed ? "PASS" : "FAIL"}
                          </span>
                        </div>
                        <p style={{ margin: "0.5rem 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>{item.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Vulnerability & PoV Details */}
            {result.vulnerability && (
              <section style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "1.5rem", marginBottom: "2rem" }}>
                <h2 style={{ fontSize: "1.1rem", margin: "0 0 1rem", color: "#f8fafc" }}>Confirmed Vulnerability Details</h2>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div>
                    <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>CWE Classification</span>
                    <p style={{ margin: "0.2rem 0", fontWeight: 600 }}>{result.vulnerability}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Sanitizer Crash Signature</span>
                    <p style={{ margin: "0.2rem 0", fontFamily: "monospace", fontSize: "0.85rem", color: "#f87171" }}>
                      {result.crash_signature || "N/A"}
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>PoV SHA-256</span>
                    <p style={{ margin: "0.2rem 0", fontFamily: "monospace", fontSize: "0.8rem", color: "#cbd5e1" }}>
                      {result.pov_sha256 || "N/A"}
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Evidence Report Path</span>
                    <p style={{ margin: "0.2rem 0", fontFamily: "monospace", fontSize: "0.8rem", color: "#38bdf8" }}>
                      {result.report_path || "N/A"}
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* Evidence Logs */}
            {result.verification && result.verification.evidence && (
              <section style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", padding: "1.5rem" }}>
                <h2 style={{ fontSize: "1.1rem", margin: "0 0 1rem", color: "#f8fafc" }}>Execution Evidence Trace</h2>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {result.verification.evidence.map((ev, index) => (
                    <details key={index} style={{ background: "#1e293b", borderRadius: "6px", padding: "0.75rem" }}>
                      <summary style={{ cursor: "pointer", fontWeight: 600, fontSize: "0.875rem", color: "#38bdf8" }}>
                        {ev.phase} — Exit Code: {ev.exit_code}
                      </summary>
                      <div style={{ marginTop: "0.75rem", fontSize: "0.8rem" }}>
                        <div style={{ marginBottom: "0.5rem" }}>
                          <span style={{ color: "#94a3b8" }}>Command: </span>
                          <code style={{ color: "#f1f5f9" }}>{JSON.stringify(ev.command)}</code>
                        </div>
                        {ev.stdout && (
                          <div style={{ marginBottom: "0.5rem" }}>
                            <span style={{ color: "#94a3b8" }}>Stdout:</span>
                            <pre style={{ background: "#0a0e17", padding: "0.5rem", borderRadius: "4px", overflowX: "auto" }}>{ev.stdout}</pre>
                          </div>
                        )}
                        {ev.stderr && (
                          <div>
                            <span style={{ color: "#94a3b8" }}>Stderr:</span>
                            <pre style={{ background: "#0a0e17", padding: "0.5rem", borderRadius: "4px", overflowX: "auto", color: "#fca5a5" }}>
                              {ev.stderr}
                            </pre>
                          </div>
                        )}
                      </div>
                    </details>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
