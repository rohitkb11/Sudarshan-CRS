export interface CommandEvidence {
  phase: string;
  command: string[];
  exit_code: number;
  stdout: string;
  stderr: string;
}

export interface VerificationResult {
  clean_rebuild: boolean;
  pov_replay: boolean;
  regression_suite: boolean;
  differential_refuzz: boolean;
  evidence: CommandEvidence[];
}

export interface PipelineResult {
  status: "verified" | "unverified" | "no_vulnerability" | "error";
  target: string;
  vulnerability?: string;
  crash_signature?: string;
  pov_path?: string;
  pov_sha256?: string;
  pov_base64?: string;
  confirmation?: CommandEvidence;
  patch_applied: boolean;
  attempts: number;
  verification?: VerificationResult;
  report_path?: string;
  patch_path?: string;
  workspace_path?: string;
  message: string;
}
