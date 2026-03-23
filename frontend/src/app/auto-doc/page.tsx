"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  FileText,
  FolderOpen,
  Loader2,
  Play,
  Presentation,
  RefreshCw,
} from "lucide-react";
import { api, type GenerationStatusResponse, type InputFile } from "@/lib/api";
import { AppShell, SectionHeader, TopBar, formatDate } from "@/components/app-shell";

const DOC_TYPES = [
  { key: "prd", label: "PRD", description: "제품 요구사항 문서", icon: FileText },
  { key: "trd", label: "TRD", description: "기술 요구사항 문서", icon: FileText },
  { key: "wbs", label: "WBS", description: "작업 분해 구조", icon: FileText },
  { key: "proposal", label: "제안서", description: "프로젝트 제안 문서", icon: FileText },
  { key: "ppt", label: "PPT", description: "발표 자료", icon: Presentation },
] as const;

const TERMINAL_STATUSES = new Set(["completed", "completed_with_errors", "failed"]);

export default function AutoDocPage() {
  const [selected, setSelected] = useState<string[]>(DOC_TYPES.map((item) => item.key));
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const { data: inputsData, isLoading: loadingInputs, refetch: refetchInputs } = useQuery({
    queryKey: ["auto-doc-inputs"],
    queryFn: () => api.listInputFiles(),
  });

  const startMutation = useMutation({
    mutationFn: () => api.generateDocuments(selected),
    onSuccess: (response) => {
      setCurrentJobId(response.job_id);
    },
  });

  const { data: statusData } = useQuery({
    queryKey: ["auto-doc-status", currentJobId],
    queryFn: () => api.getGenerationStatus(currentJobId as string),
    enabled: Boolean(currentJobId),
    refetchInterval: (query) => {
      const current = query.state.data as GenerationStatusResponse | undefined;
      if (!current) return 2000;
      return TERMINAL_STATUSES.has(current.status) ? false : 2000;
    },
  });

  const inputs = Array.isArray(inputsData?.files) ? inputsData.files : [];
  const inputFolder = inputsData?.folder_path ?? "workspace/inputs/projects";
  const selectedCount = selected.length;
  const progressPercent = statusData?.progress_percent ?? 0;
  const resultCount = Array.isArray(statusData?.results) ? statusData.results.length : 0;
  const errorCount = (Array.isArray(statusData?.errors) ? statusData.errors.length : 0) + (statusData?.error ? 1 : 0);

  function toggleDocType(docType: string) {
    setSelected((current) =>
      current.includes(docType) ? current.filter((item) => item !== docType) : [...current, docType]
    );
  }

  const statusLabel = useMemo(() => {
    if (!statusData) return "대기";
    if (statusData.status === "pending") return "대기";
    if (statusData.status === "processing") return "생성 중";
    if (statusData.status === "completed") return "완료";
    if (statusData.status === "completed_with_errors") return "부분 완료";
    if (statusData.status === "failed") return "실패";
    return statusData.status;
  }, [statusData]);

  const currentStepLabel = statusData?.current_step
    ? `${statusData.current_step_number ?? 0} / ${statusData.total_steps ?? 0} · ${statusData.current_step}`
    : "실행 전";

  return (
    <AppShell
      header={
        <TopBar
          title="자동 문서 생성"
          subtitle="입력 폴더 문서를 기준으로 필요한 산출물 세트만 선택해 실행합니다."
          href="/"
        />
      }
    >
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="section-card overflow-hidden">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                Auto-Doc
              </span>
              <h2 className="mt-5 text-3xl font-semibold tracking-[-0.05em] text-slate-900">
                선택한 산출물만 바로 실행합니다
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
                입력 확인, 문서 타입 선택, 실행 상태와 결과만 남겼습니다. 준비와 실행, 결과 확인이 한 화면에서 바로 이어지도록 단순하게 정리했습니다.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  onClick={() => startMutation.mutate()}
                  disabled={!selectedCount || !inputs.length || startMutation.isPending || (!!currentJobId && !!statusData && !["completed", "failed", "error"].includes(statusData.status))}
                  className="brand-button disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {startMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  생성 시작
                </button>
                <button onClick={() => refetchInputs()} className="secondary-button">
                  <RefreshCw className="h-4 w-4" />
                  입력 새로고침
                </button>
              </div>
            </div>

            <div className="surface-muted rounded-[30px] p-5">
              <p className="data-label">현재 실행 요약</p>
              <p className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-slate-900">
                {currentJobId ? statusLabel : "실행 대기"}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {currentJobId
                  ? statusData?.current_step
                    ? `${currentStepLabel} 단계까지 진행 중입니다.`
                    : "작업 상태를 서버에서 받아오는 중입니다."
                  : "문서 타입을 고른 뒤 실행하면 진행 상황이 여기에 표시됩니다."}
              </p>
              <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full rounded-full bg-slate-900 transition-all duration-300" style={{ width: `${progressPercent}%` }} />
              </div>
              <div className="mt-5 grid gap-3">
                <SummaryLine label="입력 문서" value={`${inputs.length}개`} />
                <SummaryLine label="선택 생성기" value={`${selectedCount}개`} />
                <SummaryLine label="결과 파일" value={`${resultCount}개`} />
                <SummaryLine label="오류 / 경고" value={`${errorCount}건`} tone={errorCount ? "warning" : "default"} />
              </div>
            </div>
          </div>
        </div>

        <aside className="section-card">
          <SectionHeader
            title="생성 세트"
            description="필요한 문서 타입만 선택합니다."
            action={
              <span className="pill-badge bg-slate-100 text-slate-700">
                {selectedCount}/{DOC_TYPES.length}
              </span>
            }
          />

          <div className="space-y-3">
            {DOC_TYPES.map((docType) => (
              <DocTypeCard
                key={docType.key}
                docType={docType}
                active={selected.includes(docType.key)}
                onToggle={() => toggleDocType(docType.key)}
              />
            ))}
          </div>

          <div className="mt-5 rounded-[24px] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] p-4">
            <p className="text-sm font-semibold text-slate-900">입력 폴더</p>
            <p className="mt-2 break-all text-xs leading-6 text-slate-500">{inputFolder}</p>
          </div>
        </aside>
      </section>

      <section className="section-card">
        <SectionHeader
          title="입력 소스"
          description="실행 전에 서버가 읽을 원본 파일 목록입니다."
          action={<span className="pill-badge bg-slate-100 text-slate-700">{inputs.length} files</span>}
        />

        <div className="mb-4 rounded-[22px] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-4 py-3 text-sm text-slate-600">
          <div className="flex items-start gap-3">
            <FolderOpen className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
            <div>
              <p className="font-medium text-slate-900">서버 입력 경로</p>
              <p className="mt-1 break-all text-xs leading-6 text-slate-500">{inputFolder}</p>
            </div>
          </div>
        </div>

        {loadingInputs ? (
          <LoadingPanel label="입력 파일을 불러오는 중입니다." />
        ) : !inputs.length ? (
          <EmptyPanel
            title="입력 폴더에 문서가 없습니다"
            description="원본 문서를 추가하면 여기에서 바로 실행 준비 상태를 확인할 수 있습니다."
          />
        ) : (
          <div className="space-y-3">
            {inputs.map((file) => (
              <InputFileRow key={file.path} file={file} />
            ))}
          </div>
        )}
      </section>

      <section className="section-card">
        <SectionHeader title="생성 결과" description="실행이 시작되면 결과 파일과 작업 메타 정보를 이곳에서 확인합니다." />
        {!currentJobId ? (
          <EmptyPanel title="아직 실행된 작업이 없습니다" description="문서 타입을 선택한 뒤 생성 시작을 누르면 결과 패널이 활성화됩니다." />
        ) : !statusData ? (
          <LoadingPanel label="작업 상태를 불러오는 중입니다." />
        ) : (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="space-y-4">
              {Array.isArray(statusData.results) && statusData.results.length ? (
                statusData.results.map((result) => (
                  <ResultRow key={`${result?.type ?? ""}-${result?.path ?? ""}`} type={result?.type ?? ""} path={result?.path ?? ""} />
                ))
              ) : (
                <EmptyPanel title="아직 생성된 결과가 없습니다" description="작업이 진행되면 결과 파일이 이곳에 누적됩니다." compact />
              )}
            </div>

            <aside className="space-y-4">
              <div className="surface-muted p-5">
                <p className="data-label">작업 정보</p>
                <div className="mt-3 space-y-2 text-sm text-slate-600">
                  <p>작업 ID: {statusData.job_id}</p>
                  <p>생성 시각: {formatDate(statusData.created_at)}</p>
                  {statusData.started_at ? <p>시작 시각: {formatDate(statusData.started_at)}</p> : null}
                  {statusData.completed_at ? <p>완료 시각: {formatDate(statusData.completed_at)}</p> : null}
                  {statusData.total_time_seconds ? <p>소요 시간: {statusData.total_time_seconds.toFixed(1)}초</p> : null}
                </div>
              </div>

              <div className="surface-muted p-5">
                <p className="data-label">오류 / 경고</p>
                {statusData.error || (Array.isArray(statusData.errors) && statusData.errors.length) ? (
                  <div className="mt-3 space-y-2 text-sm text-amber-700">
                    {statusData.error ? <p>{String(statusData.error)}</p> : null}
                    {(Array.isArray(statusData.errors) ? statusData.errors : []).map((error, idx) => (
                      <p key={`${String(error)}-${idx}`}>{String(error)}</p>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">표시할 오류가 없습니다.</p>
                )}
              </div>
            </aside>
          </div>
        )}
      </section>
    </AppShell>
  );
}

function SummaryLine({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "warning";
}) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className={tone === "warning" ? "font-semibold text-amber-700" : "font-semibold text-slate-900"}>{value}</span>
    </div>
  );
}

function DocTypeCard({
  docType,
  active,
  onToggle,
}: {
  docType: (typeof DOC_TYPES)[number];
  active: boolean;
  onToggle: () => void;
}) {
  const Icon = docType.icon;

  return (
    <button
      onClick={onToggle}
      className={`flex w-full items-start justify-between gap-4 rounded-[22px] border px-4 py-4 text-left transition ${
        active
          ? "border-slate-900 bg-slate-900 text-white shadow-[0_20px_40px_rgba(15,23,42,0.18)]"
          : "border-[var(--line-soft)] bg-white/70 text-slate-900 hover:border-slate-300"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border ${
            active ? "border-white/15 bg-white/10 text-white" : "border-[var(--line-soft)] bg-[var(--bg-panel-muted)] text-slate-700"
          }`}
        >
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold">{docType.label}</p>
          <p className={`mt-1 text-xs leading-5 ${active ? "text-white/72" : "text-slate-500"}`}>{docType.description}</p>
        </div>
      </div>
      {active ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" /> : null}
    </button>
  );
}

function InputFileRow({ file }: { file: InputFile }) {
  return (
    <div className="list-card">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold text-slate-900">{file?.name ?? ""}</p>
          <p className="mt-1 text-sm text-slate-500">
            {file?.extension || "파일"} · {formatFileSize(file?.size ?? 0)}
          </p>
          <p className="mt-2 truncate text-xs text-slate-400">{file?.path ?? ""}</p>
        </div>
      </div>
    </div>
  );
}

function ResultRow({ type, path }: { type: string; path: string }) {
  const isPresentation = type === "ppt";
  const Icon = isPresentation ? Presentation : FileText;

  return (
    <div className="list-card">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] text-slate-700">
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="pill-badge bg-slate-100 text-slate-700">{type ? type.toUpperCase() : ""}</span>
            <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" />
              저장 완료
            </span>
          </div>
          <p className="mt-2 break-all text-sm leading-6 text-slate-600">{path}</p>
        </div>
      </div>
    </div>
  );
}

function LoadingPanel({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      <p className="mt-4 text-sm text-slate-500">{label}</p>
    </div>
  );
}

function EmptyPanel({
  title,
  description,
  compact = false,
}: {
  title: string;
  description: string;
  compact?: boolean;
}) {
  return (
    <div className={`surface-muted rounded-[24px] px-6 text-center ${compact ? "py-10" : "py-16"}`}>
      <p className="text-lg font-semibold text-slate-900">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}

function formatFileSize(bytes: number) {
  const n = typeof bytes === "number" && isFinite(bytes) ? bytes : 0;
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  return `${(n / 1024).toFixed(1)} KB`;
}
