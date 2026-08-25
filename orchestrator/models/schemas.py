from typing import Literal
from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    target: str = Field(default="example-target", pattern=r"^[a-zA-Z0-9_-]+$")
    mode: Literal["full", "delta"] = "full"


class CommandEvidence(BaseModel):
    phase: str
    command: list[str]
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class VerificationResult(BaseModel):
    clean_rebuild: bool
    pov_replay: bool
    regression_suite: bool
    differential_refuzz: bool
    evidence: list[CommandEvidence] = Field(default_factory=list)


class PipelineResult(BaseModel):
    status: Literal["verified", "unverified", "no_vulnerability", "error"]
    target: str
    vulnerability: str | None = None
    crash_signature: str | None = None
    pov_path: str | None = None
    pov_sha256: str | None = None
    pov_base64: str | None = None
    confirmation: CommandEvidence | None = None
    patch_applied: bool = False
    attempts: int = 0
    verification: VerificationResult | None = None
    report_path: str | None = None
    patch_path: str | None = None
    workspace_path: str | None = None
    message: str
