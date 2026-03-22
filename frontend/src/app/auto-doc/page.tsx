"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, FileText, Loader2, Play, Presentation, Sparkles } from "lucide-react";
import { api, type GenerationStatusResponse, type InputFile } from "@/lib/api";
import { AppShell, HeroPanel, SectionHeader, TopBar, formatDate } from "@/components/app-shell";

const DOC_TYPES = [
  { key: "prd", label: "PRD", description: "제품 요구사항 문서" },
  { key: "trd", label: "TRD", description: "기술 요구사항 문서" },
  { key: "wbs", label: "WBS", description: "작업 분해 구조" },
  { key: "proposal", label: "제안서", description: "프로젝트 제안 문서" },
  { key: "ppt", label: "PPT", description: "발표 자료" },
] as const;

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
      return current.status === "completed" || current.status === "completed_with_errors" || current.status === "failed"
        ? false
        : 2000;
    },
  });

  const selectedCount = selected.length;
  const inputs = inputsData?.files ?? [];

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

  return (
    <AppShell header={<TopBar title="문서 생성 실행" subtitle="로컬 입력 폴더의 문서를 기준으로 생성기를 서버에서 실행합니다." href="/" />}>
      <HeroPanel
        kicker="Auto-Doc"
        title="에이전트를 웹에서 실행하는 전용 화면입니다"
        description="브라우저에서 직접 Python을 돌리는 것이 아니라, 서버가 기존 생성기를 대신 실행하도록 연결했습니다. 입력 폴더의 파일을 읽고 선택한 문서 타입만 생성합니다."
        actions={
          <>
            <button
              onClick={() => startMutation.mutate()}
              disabled={!selectedCount || !inputs.length || startMutation.isPending}
              className="brand-button disabled:cursor-not-allowed disabled:opacity-50"
            >
              {startMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              생성 시작
            </button>
            <button onClick={() => refetchInputs()} className="secondary-button">
              <Sparkles className="h-4 w-4" />
              입력 새로고침
            </button>
          </>
        }
        aside={
          <div className="grid gap-3 sm:grid-cols-2">
            <StatTile label="입력 파일" value={inputs.length} />
            <StatTile label="선택 생성기" value={selectedCount} />
            <StatTile label="현재 상태" value={statusLabel} />
            <StatTile label="진행률" value={`${statusData?.progress_percent ?? 0}%`} />
          </div>
        }
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="section-card">
          <SectionHeader title="입력 폴더 문서" description="`workspace/inputs/projects` 폴더를 기준으로 서버가 생성 작업을 수행합니다." />
          {loadingInputs ? (
            <LoadingPanel label="입력 파일을 불러오는 중입니다." />
          ) : !inputs.length ? (
            <EmptyPanel title="입력 폴더에 문서가 없습니다" description="`workspace/inputs/projects` 폴더에 원본 문서를 넣으면 여기서 바로 실행할 수 있습니다." />
          ) : (
            <div className="space-y-3">
              {inputs.map((file) => (
                <InputFileRow key={file.path} file={file} />
              ))}
            </div>
          )}
        </div>

        <aside className="section-card">
          <SectionHeader title="생성할 문서 타입" description="필요한 생성기만 골라서 실행할 수 있습니다." />
          <div className="space-y-3">
            {DOC_TYPES.map((docType) => {
              const active = selected.includes(docType.key);
              return (
                <button
                  key={docType.key}
                  onClick={() => toggleDocType(docType.key)}
                  className={`flex w-full items-start justify-between rounded-[18px] border px-4 py-4 text-left transition ${
                    active ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-900"
                  }`}
                >
                  <div>
                    <p className="text-sm font-semibold">{docType.label}</p>
                    <p className={`mt-1 text-xs ${active ? "text-white/70" : "text-slate-500"}`}>{docType.description}</p>
                  </div>
                  {active ? <CheckCircle2 className="h-4 w-4" /> : null}
                </button>
              );
            })}
          </div>
        </aside>
      </section>

      <section className="section-card">
        <SectionHeader title="실행 상태" description="현재 작업의 단계, 결과 파일, 오류를 실시간에 가깝게 확인합니다." />
        {!currentJobId ? (
          <EmptyPanel title="아직 실행된 작업이 없습니다" description="문서 타입을 선택한 뒤 생성 시작 버튼을 누르면 여기서 상태를 볼 수 있습니다." />
        ) : !statusData ? (
          <LoadingPanel label="작업 상태를 불러오는 중입니다." />
        ) : (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="space-y-4">
              <div className="surface-muted p-5">
                <p className="data-label">현재 단계</p>
                <p className="mt-3 text-lg font-semibold text-slate-900">
                  {statusData.current_step ? `${statusData.current_step_number} / ${statusData.total_steps} · ${statusData.current_step}` : statusLabel}
                </p>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-slate-900" style={{ width: `${statusData.progress_percent ?? 0}%` }} />
                </div>
              </div>

              <div>
                <p className="mb-3 text-sm font-semibold text-slate-900">결과 파일</p>
                {statusData.results.length ? (
                  <div className="space-y-3">
                    {statusData.results.map((result) => (
                      <div key={`${result.type}-${result.path}`} className="list-card">
                        <div className="flex items-center gap-3">
                          {result.type === "ppt" ? <Presentation className="h-5 w-5 text-slate-500" /> : <FileText className="h-5 w-5 text-slate-500" />}
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-900">{result.type.toUpperCase()}</p>
                            <p className="truncate text-xs text-slate-500">{result.path}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">아직 생성된 결과가 없습니다.</p>
                )}
              </div>
            </div>

            <aside className="space-y-4">
              <div className="surface-muted p-5">
                <p className="data-label">작업 정보</p>
                <div className="mt-3 space-y-2 text-sm text-slate-600">
                  <p>작업 ID: {statusData.job_id}</p>
                  <p>생성 시각: {formatDate(statusData.created_at)}</p>
                  {statusData.completed_at ? <p>완료 시각: {formatDate(statusData.completed_at)}</p> : null}
                  {statusData.total_time_seconds ? <p>소요 시간: {statusData.total_time_seconds.toFixed(1)}초</p> : null}
                </div>
              </div>

              <div className="surface-muted p-5">
                <p className="data-label">오류 / 경고</p>
                {statusData.error || statusData.errors.length ? (
                  <div className="mt-3 space-y-2 text-sm text-rose-700">
                    {statusData.error ? <p>{statusData.error}</p> : null}
                    {statusData.errors.map((error) => (
                      <p key={error}>{error}</p>
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

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="surface-muted p-4">
      <p className="data-label">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
    </div>
  );
}

function InputFileRow({ file }: { file: InputFile }) {
  return (
    <div className="list-card">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold text-slate-900">{file.name}</p>
          <p className="mt-1 text-sm text-slate-500">
            {file.extension || "파일"} · {(file.size / 1024).toFixed(1)} KB
          </p>
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

function EmptyPanel({ title, description }: { title: string; description: string }) {
  return (
    <div className="surface-muted rounded-[24px] px-6 py-16 text-center">
      <p className="text-lg font-semibold text-slate-900">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}
