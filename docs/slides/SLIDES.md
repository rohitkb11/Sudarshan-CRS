# AI Kavach (Sudarshan-CRS) — 5-Slide Pitch Deck Specification
**Competition**: Terrier Cyber Quest 2026 — Indian Army (AI Kavach Track)

---

## Slide 1: Introduction, Ideation & Brief Description

### Title
**AI KAVACH — Autonomous Cyber-Reasoning System (CRS)**
*Find the bug. Prove it's real. Fix it. Prove the fix holds. All without a human in the loop.*

### Problem
- Modern defence and national security software infrastructures are millions of lines of code with complex dependencies.
- Manual vulnerability hunting and patch verification are too slow to keep pace with zero-day attacks.
- Traditional "AI wrapper" approaches fail because they throw massive LLMs at entire repositories—leading to hallucinations, slow execution, and high cloud compute costs.

### Our Solution
- **Sudarshan-CRS** is an autonomous, lightweight Cyber-Reasoning System engineered after DARPA AIxCC top-performing architectures (Trail of Bits' *Buttercup*).
- Decomposes cybersecurity reasoning into deterministic tools (LLVM Sanitizers, libFuzzer/AFL++, Semgrep) for heavy lifting, invoking ultra-fast reasoning LLMs (Groq LPU / Qwen 27B) only where human judgment is needed.

---

## Slide 2: Detailed Methodology (The 7-Stage Pipeline)

### Pipeline Flow
1. **Stage 1 — Task Intake & Disposable Build**: Compiles target in Normal, Sanitized (ASan+UBSan), and Fuzzer modes in clean container.
2. **Stage 2 — Parallel Discovery**: Semgrep static analysis guides targeted seed generation for libFuzzer campaigns.
3. **Stage 3 — Context Map**: Lightweight AST code index provides tight function slices instead of massive prompt context.
4. **Stage 4 — PoV Confirmation**: Replays crashing input deterministically under sanitizers to establish ground truth proof.
5. **Stage 5 — Tiered Patch Generation**: 
   - *Tier 1*: Deterministic Rule Registry (instant template patches).
   - *Tier 2*: Patch Memory (Case-Based Reasoning store of past verified fixes).
   - *Tier 3*: LLM Reasoning (Groq Qwen/Llama with failure feedback).
6. **Stage 6 — Verification Suite (V1–V4 Proof Checklist)**: Clean rebuild $\to$ PoV replay $\to$ Regression suite $\to$ Differential re-fuzzing (capped at 3 feedback retries).
7. **Stage 7 — Evidence Reporting**: Packages cryptographic proof, sanitizer before/after stderr, and plain-language root cause explanation.

---

## Slide 3: Technology Stack & Architecture Diagram

### System Architecture
```
+-----------------------------------------------------------------------------------+
|                           AI KAVACH CRS ARCHITECTURE                              |
+-----------------------------------------------------------------------------------+
|  [Target Codebase] ---> [Stage 1: Build Harness] (Normal / ASan+UBSan / Fuzzer)  |
|                                    |                                              |
|                                    v                                              |
|      +---------------------------------------------------------------------+      |
|      | [Stage 2: Discovery Engine]  <--->  [Stage 3: AST Context Map]      |      |
|      | - libFuzzer / AFL++ Engine          - Call Graph & Function Index   |      |
|      | - Semgrep Static Analysis           - Targeted Code Slicing         |      |
|      +---------------------------------------------------------------------+      |
|                                    |                                              |
|                                    v                                              |
|                   [Stage 4: Confirmed PoV Replay]                                 |
|                                    |                                              |
|                                    v                                              |
|      +---------------------------------------------------------------------+      |
|      | [Stage 5: Tiered Patch Generation] <--> [Patch Memory CBR Store]    |      |
|      | 1. Rule Registry (Instant)             - JSONL / SQLite Precedents  |      |
|      | 2. Memory Precedent Matching                                        |      |
|      | 3. Groq LPU Reasoning (Qwen 27B / Llama 3.3)                         |      |
|      +---------------------------------------------------------------------+      |
|                                    |                                              |
|                                    v                                              |
|      +---------------------------------------------------------------------+      |
|      | [Stage 6: Verification Suite (V1-V4)]                                |      |
|      |  V1 Clean Rebuild | V2 PoV Replay | V3 Regression | V4 Diff Re-Fuzz |      |
|      +---------------------------------------------------------------------+      |
|                               |                     |                             |
|                    (Fail: Retry <= 3)          (Pass: Proven)                     |
|                               |                     |                             |
|                               +----------------->   v                             |
|                                           [Stage 7: Evidence Report & UI]         |
+-----------------------------------------------------------------------------------+
```

### Technology Matrix
- **Core Orchestrator**: Python 3.12, FastAPI, Uvicorn
- **Dynamic Analysis**: LLVM Clang, AddressSanitizer (ASan), UndefinedBehaviorSanitizer (UBSan), libFuzzer, AFL++
- **Static Analysis**: Semgrep with custom military/C security rules
- **AI Reasoning**: Groq LPU API (`qwen/qwen3.6-27b`, `llama-3.3-70b`), Anthropic Claude Fallback
- **Frontend / Console**: React 18, Vite, TypeScript
- **Containerization**: Docker Compose (`no-new-privileges`, `cap_drop: ALL`)

---

## Slide 4: Salient Features & Novelty / USP

### 1. §8 Definition of Proof (Beyond Naive Patching)
In DARPA AIxCC, ~40% of patches that passed basic compile checks were semantically wrong. Sudarshan-CRS enforces **Differential Re-Fuzzing (V4)** to guarantee the patch does not just hide the crash.

### 2. Patch Memory (Case-Based Reasoning)
Learns from every verified fix. The system becomes faster, cheaper, and more deterministic over time without retraining weights or spending unnecessary tokens.

### 3. Dual Scan Modes: Full Scan vs Delta Scan
Enables instant CI/CD Pull Request auditing (Delta Scan) by focusing AST context and fuzzing budgets exclusively on incoming code diffs.

### 4. Hardware Efficiency (Laptop / Edge Deployable)
Engineered for constrained edge or air-gapped environments. Does not require cluster GPUs; runs within 8 cores, 16GB RAM, and containerized sandboxes.

---

## Slide 5: Final Deliverables

### Concrete Outputs
1. **Fully Autonomous CRS Engine**: Single-command execution via REST API (`POST /scans`) or web console.
2. **Cryptographic PoV Artifacts**: Exact crashing input payloads with SHA-256 digests and base64 encoding.
3. **Verified Unified Diffs (`.patch`)**: Clean, drop-in patches passing compiler and regression gates.
4. **Comprehensive Evidence Dossier**: Markdown & JSON reports with execution traces, before/after sanitizer dumps, and V1–V4 checklists.
5. **Interactive Commander Dashboard**: Real-time evidence visualization console for evaluation juries and defence engineers.
