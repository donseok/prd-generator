"use client";

import { useEffect, type ReactNode } from "react";
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
  Target,
  Wand2,
} from "lucide-react";
import { api } from "@/lib/api";
import { AppShell, HeroPanel, SectionHeader, TopBar, formatDate } from "@/components/app-shell";

const LAYERS = [
  {
    key: "parsing",
    name: "입력 해석",
    description: "원본 문서에서 텍스트와 구조, 첨부 단서를 추출합니다.",
    icon: ScanSearch,
    accent: "bg-blue-600",
    ring: "ring-blue-200",
    surface: "bg-blue-50 border-blue-200",
  },
  {
    key: "normalizing",
    name: "요구사항 정규화",
    description: "중복 표현을 합치고 의미 단위를 요구사항 구조로 정리합니다.",
    icon: Wand2,
    accent: "bg-violet-600",
    ring: "ring-violet-200",
    surface: "bg-violet-50 border-violet-200",
  },
  {
    key: "validating",
    name: "검증 및 리뷰 분기",
    description: "신뢰도와 누락 정보, 충돌 가능성을 점검합니다.",
    icon: CheckCircle2,
    accent: "bg-amber-500",
    ring: "ring-amber-200",
    surface: "bg-amber-50 border-amber-200",
  },
  {
    key: "generating",
    name: "문서 생성",
    description: "최종 PRD와 후속 산출물을 생성합니다.",
    icon: Sparkles,
    accent: "bg-emerald-600",
    ring: "ring-emerald-200",
    surface: "bg-emerald-50 border-emerald-200",
  },
];

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

  useEffect(() => {
    if (status?.status === "completed" && status.prd_id) {
      router.push(`/prd/${status.prd_id}`);
      return;
    }
    if (status?.status === "pm_review") {
      router.push(`/review/${jobId}`);
    }
  }, [jobId, router, status]);

  const currentLayerIndex = LAYERS.findIndex((layer) => layer.key === status?.current_layer);
  const progress = status?.progress_percent ?? 0;

  return (
    <AppShell header={<TopBar title="처리 상태" subtitle={jobId} href="/upload" />}>
      <HeroPanel
        kicker="실시간 파이프라인"
        title="문서 생성 과정을 단계별로 추적하고 있습니다"
        description="현재 레이어를 크게 강조하고, 다음 화면 이동까지 자연스럽게 이어지도록 처리 보드를 다시 구성했습니다. 완료 시에는 상세 문서로, 검토가 필요한 경우에는 리뷰 화면으로 자동 이동합니다."
        aside={
          <div className="space-y-4">
            <div>
              <p className="data-label">진행률</p>
              <p className="mt-2 text-4xl font-semibold tracking-tight text-slate-900">{progress}%</p>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-slate-200">
              <div className="h-full rounded-full" style={{ width: `${progress}%`, background: "var(--gradient-brand)" }} />
            </div>
            {status ? (
              <div className="surface-muted p-4">
                <p className="data-label">마지막 업데이트</p>
                <p className="mt-2 text-sm font-medium text-slate-700">{formatDate(status.updated_at)}</p>
              </div>
            ) : null}
          </div>
        }
      />

      {error ? (
        <StateMessage
          icon={<AlertCircle className="h-10 w-10 text-rose-500" />}
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
          icon={<AlertCircle className="h-10 w-10 text-rose-500" />}
          title="처리 작업이 실패했습니다"
          description={status.error ?? "알 수 없는 오류로 작업이 중단되었습니다."}
          action={
            <Link href="/upload" className="brand-button">
              다시 업로드
            </Link>
          }
        />
      ) : (
        <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="section-card">
            <SectionHeader
              title="레이어 진행 보드"
              description="완료 단계와 현재 진행 단계가 확실히 보이도록 카드 보드로 정리했습니다."
            />
            <div className="space-y-4">
              {LAYERS.map((layer, index) => {
                const isComplete = status.status === "completed" || index < currentLayerIndex;
                const isCurrent = index === currentLayerIndex && status.status !== "completed";
                const Icon = layer.icon;

                return (
                  <div
                    key={layer.key}
                    className={`rounded-[28px] border p-5 transition ${
                      isCurrent
                        ? `${layer.surface} ring-4 ${layer.ring}`
                        : isComplete
                        ? "border-emerald-200 bg-emerald-50"
                        : "border-slate-200 bg-white/65"
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div
                        className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-[22px] text-white ${
                          isComplete ? "bg-emerald-600" : isCurrent ? layer.accent : "bg-slate-300"
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
                          <p className="text-lg font-semibold tracking-tight text-slate-900">{layer.name}</p>
                          <span
                            className={`pill-badge ${
                              isComplete
                                ? "bg-emerald-100 text-emerald-700"
                                : isCurrent
                                ? "bg-slate-900 text-white"
                                : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {isComplete ? "완료" : isCurrent ? "진행 중" : "대기"}
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-600">{layer.description}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <aside className="section-card">
            <SectionHeader title="입력 문서" description="현재 작업에 포함된 원본 파일입니다." />
            <div className="space-y-3">
              {status.documents?.length ? (
                status.documents.map((document) => (
                  <div key={document} className="surface-muted flex items-center gap-3 px-4 py-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white">
                      <FileText className="h-4 w-4" />
                    </div>
                    <p className="min-w-0 truncate text-sm font-medium text-slate-700">{document}</p>
                  </div>
                ))
              ) : (
                <div className="surface-muted px-4 py-5 text-sm text-slate-500">등록된 파일이 없습니다.</div>
              )}
            </div>

            <div className="mt-6 grid gap-4">
              <div className="surface-muted p-5">
                <p className="data-label">다음 이동</p>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  작업이 완료되면 상세 PRD 화면으로 이동하고, 사람이 판단해야 할 항목이 있으면 PM 리뷰 화면으로 자동 전환됩니다.
                </p>
              </div>
              <div className="surface-muted p-5">
                <p className="data-label">현재 상태</p>
                <div className="mt-3 flex items-center gap-2 text-sm font-medium text-slate-700">
                  <Target className="h-4 w-4 text-blue-600" />
                  {status.status}
                </div>
              </div>
            </div>
          </aside>
        </section>
      )}
    </AppShell>
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
        <p className="mt-5 text-2xl font-semibold tracking-tight text-slate-900">{title}</p>
        <p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">{description}</p>
        {action ? <div className="mt-6">{action}</div> : null}
      </div>
    </section>
  );
}
