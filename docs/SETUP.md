# Local setup and runtime requirements

This guide is deliberately separate from the project architecture brief in `README.md`.

## Recommended environment: Docker Desktop on Windows

The prototype compiles C targets with AddressSanitizer (ASan) and UndefinedBehaviorSanitizer (UBSan). Use Docker's Linux environment for reliable sanitizer support.

### Prerequisites

1. Windows 10/11 with virtualization enabled.
2. Windows Subsystem for Linux 2 (WSL 2).
3. Docker Desktop, configured to use the WSL 2 backend.

Install WSL from an Administrator PowerShell session, then restart if requested:

```powershell
wsl --install
```

Install Docker Desktop after WSL has finished its first-run setup. In Docker Desktop settings, enable **Use the WSL 2 based engine** and WSL integration for the installed Linux distribution.

Verify the installation:

```powershell
docker --version
docker compose version
```

## Run the prototype

From the repository root:

```powershell
docker compose up --build
```

Wait until Uvicorn reports that it is listening on port 8000. In another PowerShell terminal, submit the included safe demo target:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/scans -ContentType 'application/json' -Body '{"target":"example-target","mode":"full"}'
```

Expected result: a `verified` response with V1–V4 verification fields, a Markdown evidence report under `data/reports/`, and a verified Patch Memory entry at `data/patch_memory.jsonl`.

Stop the service with `Ctrl+C` or:

```powershell
docker compose down
```

## Native development alternative

Native Windows support varies because ASan/UBSan support is a compiler/runtime concern. Docker is preferred. If developing locally, install:

- Python 3.12 or 3.13
- LLVM/Clang with ASan and UBSan runtimes
- GNU Make

Then create a virtual environment and run the API:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:CLANG_BIN = "clang"
$env:MAKE_BIN = "make"
uvicorn orchestrator.main:app --reload
```

The current machine has Python 3.14 and MSYS2 GCC, but its GCC installation does not include `libasan`/`libubsan`; it cannot execute the sanitizer-backed demo until a complete LLVM/Docker environment is available.

## Security boundary

Run scans only against source code and environments you own or are expressly authorized to test. The bundled target is an intentionally vulnerable local demonstration fixture.
