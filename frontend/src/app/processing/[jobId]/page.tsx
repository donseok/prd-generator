"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  ScanSearch,
  Sparkles,
  Wand2,
} from "lucide-react";
import { api } from "@/lib/api";
import { AppShell, SectionHeader, TopBar, formatDate } from "@/components/app-shell";

const LAYERS = [
  {
    key: "parsing",
    name: "입력 해석",
    description: "원본 문서에서 텍스트와 구조, 단서를 추출합니다.",
    icon: ScanSearch,
  },
  {
    key: "normalizing",
    name: "요구사항 정규화",
    description: "표현을 정리하고 의미 단위를 요구사항 구조로 합칩니다.",
    icon: Wand2,
  },
  {
    key: "validating",
    name: "검증 및 리뷰 분기",
    description: "신뢰도, 누락 정보, 충돌 가능성을 점검합니다.",
    icon: CheckCircle2,
  },
  {
    key: "generating",
    name: "문서 생성",
    description: "최종 PRD와 후속 산출물을 생성합니다.",
    icon: Sparkles,
  },
] as const;

const STATUS_LABELS: Record<string, string> = {
  pending: "대기",
  parsing: "입력 해석 중",
  normalizing: "정규화 중",
  validating: "검증 중",
  generating: "생성 중",
  completed: "완료",
  failed: "실패",
  pm_review: "PM 검토 필요",
};

export default function ProcessingPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  const { data: status, error } = useQuery({
    queryKey: ["processing", jobId],
    queryFn: () => api.getProcessingStatus(jobId),
    refetchInterval: (query) => {
      const current = query.state.data;
      if (!current) return 2000;
      if (current.status === "completed" || current.status === "failed" || current.status === "pm_review") return false;
      return 2000;
    },
  });

  const hasRedirected = useRef(false);

  useEffect(() => {
    if (hasRedirected.current) return;
    if (status?.status === "completed" && status.prd_id) {
      hasRedirected.current = true;
      router.push(`/prd/${status.prd_id}`);
      return;
    }
    if (status?.status === "pm_review") {
      hasRedirected.current = true;
      router.push(`/review/${jobId}`);
    }
  }, [jobId, router, status]);

  const currentLayerIndex = LAYERS.findIndex((layer) => layer.key === status?.current_layer);
  const progress = status?.progress_percent ?? 0;
  const currentStatusLabel = status ? STATUS_LABELS[status.status] ?? status.status : "연결 중";

  return (
    <AppShell header={<TopBar title="처리 상태" subtitle={jobId} href="/upload" />}>
      {error ? (
        <StateMessage
          icon={<AlertCircle className="h-10 w-10 text-orange-600" />}
          title="작업 상태를 불러오지 못했습니다"
          description="잠시 후 다시 시도하거나 새 업로드 작업을 시작해 주세요."
          action={
            <Link href="/upload" className="brand-button">
              새 작업 시작
            </Link>
          }
        />
      ) : !status ? (
        <StateMessage
          icon={<Loader2 className="h-10 w-10 animate-spin text-slate-400" />}
          title="작업 상태를 연결하는 중입니다"
          description="처음 응답을 기다리고 있습니다."
        />
      ) : status.status === "failed" ? (
        <StateMessage
          icon={<AlertCircle className="h-10 w-10 text-orange-600" />}
          title="처리 작업이 실패했습니다"
          description={status.error ?? "알 수 없는 오류로 작업이 중단되었습니다."}
          action={
            <Link href="/upload" className="brand-button">
              다시 업로드
            </Link>
          }
        />
      ) : (
        <>
          <section className="section-card">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
              <div>
                <p className="data-label">실시간 파이프라인</p>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <h2 className="text-3xl font-semibold tracking-[-0.05em] text-slate-900">{progress}% 진행 중</h2>
                  <span className="pill-badge bg-slate-100 text-slate-700">{currentStatusLabel}</span>
                </div>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
                  현재 단계와 다음 이동을 한 화면에서 바로 파악할 수 있도록 작업판 형태로 재구성했습니다. 완료 시에는 상세 PRD로, 검토가 필요한 경우에는 리뷰 화면으로 자동 이동합니다.
                </p>
                <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-slate-900 transition-all duration-500" style={{ width: `${progress}%` }} />
                </div>
              </div>

              <aside className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <SummaryCard label="현재 단계" value={status.current_layer ? LAYERS.find((layer) => layer.key === status.current_layer)?.name ?? status.current_layer : currentStatusLabel} />
                <SummaryCard label="마지막 업데이트" value={formatDate(status.updated_at)} />
                <SummaryCard label="입력 문서" value={`${Array.isArray(status.documents) ? status.documents.length : 0}개`} />
              </aside>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="section-card">
              <SectionHeader title="레이어 진행 보드" description="전체 흐름 안에서 현재 단계가 어디인지 명확하게 보여줍니다." />
              <div className="space-y-4">
                {LAYERS.map((layer, index) => {
                  const isComplete = status.status === "completed" || index < currentLayerIndex;
                  const isCurrent = index === currentLayerIndex && status.status !== "completed";
                  const Icon = layer.icon;

                  return (
                    <div
                      key={layer.key}
                      className={`rounded-[1.3rem] border p-5 transition ${
                        isCurrent
                          ? "border-slate-900 bg-slate-900 text-white shadow-[0_18px_32px_rgba(23,33,43,0.18)]"
                          : isComplete
                          ? "border-emerald-200 bg-emerald-50"
                          : "border-[var(--line-soft)] bg-[var(--bg-panel)]"
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <div
                          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${
                            isCurrent ? "bg-white/14 text-white" : isComplete ? "bg-emerald-100 text-emerald-700" : "bg-[var(--bg-panel-muted)] text-slate-600"
                          }`}
                        >
                          {isCurrent ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                          ) : isComplete ? (
                            <CheckCircle2 className="h-5 w-5" />
                          ) : (
                            <Icon className="h-5 w-5" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-3">
                            <p className={`text-base font-semibold tracking-tight ${isCurrent ? "text-white" : "text-slate-900"}`}>{layer.name}</p>
                            <span
                              className={`pill-badge ${
                                isComplete
                                  ? "bg-emerald-100 text-emerald-700"
                                  : isCurrent
                                  ? "bg-white/14 text-white"
                                  : "bg-slate-100 text-slate-500"
                              }`}
                            >
                              {isComplete ? "완료" : isCurrent ? "진행 중" : "대기"}
                            </span>
                          </div>
                          <p className={`mt-2 text-sm leading-6 ${isCurrent ? "text-white/70" : "text-slate-600"}`}>{layer.description}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <aside className="grid gap-4">
              <section className="section-card">
                <SectionHeader title="입력 문서" description="현재 작업에 포함된 원본 파일입니다." />
                <div className="space-y-3">
                  {Array.isArray(status.documents) && status.documents.length > 0 ? (
                    status.documents.map((document, idx) => {
                      const docLabel = typeof document === "string" || typeof document === "number"
                        ? String(document)
                        : (document as { name?: string; filename?: string } | null)?.name
                          ?? (document as { name?: string; filename?: string } | null)?.filename
                          ?? String(idx + 1);
                      const docKey = typeof document === "string" || typeof document === "number"
                        ? String(document)
                        : `doc-${idx}`;
                      return (
                        <div key={docKey} className="surface-muted flex items-center gap-3 px-4 py-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--bg-panel)] text-slate-700">
                            <FileText className="h-4 w-4" />
                          </div>
                          <p className="min-w-0 truncate text-sm font-medium text-slate-700">{docLabel}</p>
                        </div>
                      );
                    })
                  ) : (
                    <div className="surface-muted px-4 py-5 text-sm text-slate-500">등록된 파일이 없습니다.</div>
                  )}
                </div>
              </section>

              <section className="section-card">
                <SectionHeader title="다음 이동" description="작업 완료 후 자동 전환되는 흐름입니다." />
                <div className="space-y-3">
                  <div className="surface-muted px-4 py-4">
                    <p className="data-label">완료 시</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">PRD 상세 화면으로 자동 이동합니다.</p>
                  </div>
                  <div className="surface-muted px-4 py-4">
                    <p className="data-label">검토 필요 시</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">PM 리뷰 화면으로 자동 전환됩니다.</p>
                  </div>
                </div>
              </section>
            </aside>
          </section>
        </>
      )}
    </AppShell>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="surface-muted p-4">
      <p className="data-label">{label}</p>
      <p className="mt-2 text-sm font-semibold leading-6 text-slate-900">{value}</p>
    </div>
  );
}

function StateMessage({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <section className="section-card">
      <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
        {icon}
        <p className="mt-5 text-xl font-semibold tracking-tight text-slate-900">{title}</p>
        <p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">{description}</p>
        {action ? <div className="mt-6">{action}</div> : null}
      </div>
    </section>
  );
}
