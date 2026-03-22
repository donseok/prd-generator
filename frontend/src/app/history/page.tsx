"use client";

import { useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Download, FileSearch, Loader2, Plus, Search, Trash2 } from "lucide-react";
import { api, type PRDListItem } from "@/lib/api";
import { AppShell, HeroPanel, MetricCard, SectionHeader, TopBar, formatDate, scoreBadge } from "@/components/app-shell";

const ITEMS_PER_PAGE = 10;

const STATUS_LABELS: Record<string, string> = {
  draft: "초안",
  review: "검토 중",
  approved: "승인",
  completed: "완료",
};

export default function HistoryPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["prds", page],
    queryFn: () => api.listPRDs(page * ITEMS_PER_PAGE, ITEMS_PER_PAGE),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deletePRD(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["prds"] }),
  });

  const prds = useMemo(() => data?.prds ?? [], [data?.prds]);
  const totalCount = data?.total ?? 0;
  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

  const filteredPrds = useMemo(() => {
    if (!searchQuery) return prds;
    return prds.filter((prd) => prd.title.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [prds, searchQuery]);

  const highlight = filteredPrds[0];
  const avgConfidence = filteredPrds.length
    ? Math.round(filteredPrds.reduce((sum, item) => sum + item.overall_confidence, 0) / filteredPrds.length / 0.01) / 100
    : 0;

  async function handleExport(id: string, format: "markdown" | "json" | "html") {
    try {
      const content = await api.exportPRD(id, format);
      const blob = new Blob([typeof content === "string" ? content : JSON.stringify(content, null, 2)], {
        type: format === "json" ? "application/json" : "text/plain",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `prd-${id}.${format === "markdown" ? "md" : format}`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (exportError) {
      console.error("문서 내보내기에 실패했습니다.", exportError);
      alert("문서 내보내기에 실패했습니다.");
    }
  }

  function handleDelete(id: string, title: string) {
    if (confirm(`"${title}" 문서를 삭제하시겠습니까?`)) {
      deleteMutation.mutate(id);
    }
  }

  return (
    <AppShell
      header={
        <TopBar
          title="PRD 아카이브"
          subtitle={`전체 ${totalCount}개 문서`}
          href="/"
          action={
            <Link href="/upload" className="brand-button">
              <Plus className="h-4 w-4" />
              새 PRD 만들기
            </Link>
          }
        />
      }
    >
      <HeroPanel
        kicker="문서 라이브러리"
        title="완성된 PRD를 탐색하고 다시 꺼내보는 공간입니다"
        description="검색, 상태 확인, 내보내기, 삭제까지 한 흐름 안에서 처리하도록 아카이브를 다시 구성했습니다. 최근 문서는 더 크게 보여주고, 나머지 문서는 카드 리스트로 빠르게 훑을 수 있게 정리했습니다."
        aside={
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="surface-muted p-4">
                <p className="data-label">현재 페이지</p>
                <p className="mt-2 text-3xl font-black tracking-[-0.06em] text-slate-900">
                  {totalPages ? page + 1 : 0}
                  <span className="ml-2 text-base font-medium text-slate-400">/ {totalPages || 0}</span>
                </p>
              </div>
              <div className="surface-muted p-4">
                <p className="data-label">페이지당 문서</p>
                <p className="mt-2 text-3xl font-black tracking-[-0.06em] text-slate-900">{ITEMS_PER_PAGE}</p>
              </div>
            </div>
            <div className="surface-muted flex items-center gap-3 px-4 py-3">
              <FileSearch className="h-5 w-5 text-slate-400" />
              <p className="text-sm leading-6 text-slate-600">최근 생성 문서를 우선 노출하고, 검색 결과는 현재 페이지 기준으로 즉시 필터링합니다.</p>
            </div>
          </div>
        }
      />

      <section className="grid gap-4 lg:grid-cols-3">
        <MetricCard label="현재 목록" value={filteredPrds.length} note="화면에 표시 중인 문서 수" />
        <MetricCard label="평균 신뢰도" value={`${Math.round(avgConfidence * 100)}%`} note="현재 목록 기준 평균 점수" accent="warm" />
        <MetricCard
          label="최근 문서 상태"
          value={highlight ? STATUS_LABELS[highlight.status] ?? highlight.status : "-"}
          note={highlight ? highlight.title : "표시할 문서가 없습니다."}
          accent="mint"
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside className="section-card">
          <SectionHeader title="추천 문서" description="가장 최근에 보이는 문서를 대표 카드로 강조했습니다." />
          {highlight ? (
            <FeaturedCard prd={highlight} />
          ) : (
            <CenteredState
              icon={<FileSearch className="h-10 w-10 text-slate-300" />}
              title="표시할 문서가 없습니다"
              action={
                <Link href="/upload" className="brand-button">
                  첫 PRD 만들기
                </Link>
              }
            />
          )}
        </aside>

        <section className="section-card">
          <SectionHeader title="문서 목록" description="제목으로 검색하고 원하는 형식으로 바로 내보낼 수 있습니다." />
          <div className="relative mb-6">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="문서 제목 검색"
              className="input-surface pl-12"
            />
          </div>

          {isLoading ? (
            <CenteredState icon={<Loader2 className="h-10 w-10 animate-spin text-slate-400" />} title="문서 목록을 불러오는 중입니다" />
          ) : error ? (
            <CenteredState icon={<FileSearch className="h-10 w-10 text-rose-500" />} title="문서 목록을 불러오지 못했습니다" />
          ) : filteredPrds.length === 0 ? (
            <CenteredState
              icon={<FileSearch className="h-10 w-10 text-slate-300" />}
              title={searchQuery ? "검색 결과가 없습니다" : "아직 저장된 문서가 없습니다"}
              action={
                !searchQuery ? (
                  <Link href="/upload" className="brand-button">
                    첫 PRD 만들기
                  </Link>
                ) : undefined
              }
            />
          ) : (
            <>
              <div className="space-y-3">
                {filteredPrds.map((prd, index) => (
                  <PRDCard
                    key={prd.id}
                    prd={prd}
                    isFeatured={index === 0}
                    onDelete={() => handleDelete(prd.id, prd.title)}
                    onExport={(format) => handleExport(prd.id, format)}
                    isDeleting={deleteMutation.isPending}
                  />
                ))}
              </div>

              {totalPages > 1 ? (
                <div className="mt-6 flex items-center justify-center gap-3">
                  <button
                    onClick={() => setPage((current) => Math.max(0, current - 1))}
                    disabled={page === 0}
                    className="secondary-button disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    이전
                  </button>
                  <span className="text-sm font-medium text-slate-500">
                    {page + 1} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((current) => Math.min(totalPages - 1, current + 1))}
                    disabled={page >= totalPages - 1}
                    className="secondary-button disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    다음
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              ) : null}
            </>
          )}
        </section>
      </section>
    </AppShell>
  );
}

function FeaturedCard({ prd }: { prd: PRDListItem }) {
  const badge = scoreBadge(prd.overall_confidence);

  return (
    <Link href={`/prd/${prd.id}`} className="block">
      <div className="glass-panel-strong overflow-hidden rounded-[30px] p-6">
        <div className="mb-5 flex flex-wrap items-center gap-2">
          <span className={`pill-badge ${badge.className}`}>신뢰도 {badge.label}</span>
          <span className="pill-badge bg-slate-100 text-slate-600">{STATUS_LABELS[prd.status] ?? prd.status}</span>
        </div>
        <p className="text-2xl font-black tracking-[-0.05em] text-slate-900">{prd.title}</p>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          요구사항 {prd.requirements_count}개가 정리된 문서입니다. 상세 화면에서 개요, 마일스톤, 미해결 이슈까지 이어서 확인할 수 있습니다.
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <div className="surface-muted p-4">
            <p className="data-label">생성일</p>
            <p className="mt-2 text-sm font-semibold text-slate-800">{formatDate(prd.created_at)}</p>
          </div>
          <div className="surface-muted p-4">
            <p className="data-label">요구사항</p>
            <p className="mt-2 text-sm font-semibold text-slate-800">{prd.requirements_count}개</p>
          </div>
        </div>
      </div>
    </Link>
  );
}

function PRDCard({
  prd,
  isFeatured,
  onDelete,
  onExport,
  isDeleting,
}: {
  prd: PRDListItem;
  isFeatured?: boolean;
  onDelete: () => void;
  onExport: (format: "markdown" | "json" | "html") => void;
  isDeleting: boolean;
}) {
  const badge = scoreBadge(prd.overall_confidence);

  return (
    <div className={`list-card ${isFeatured ? "ring-1 ring-blue-200/80" : ""}`}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            {isFeatured ? <span className="pill-badge bg-blue-100 text-blue-700">최근 문서</span> : null}
            <span className={`pill-badge ${badge.className}`}>{badge.label}</span>
            <span className="pill-badge bg-slate-100 text-slate-600">{STATUS_LABELS[prd.status] ?? prd.status}</span>
          </div>
          <Link href={`/prd/${prd.id}`} className="mt-3 block">
            <p className="truncate text-xl font-bold tracking-[-0.04em] text-slate-900">{prd.title}</p>
          </Link>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-slate-500">
            <span>{formatDate(prd.created_at)}</span>
            <span>요구사항 {prd.requirements_count}개</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <ExportButton label="MD" onClick={() => onExport("markdown")} />
          <ExportButton label="JSON" onClick={() => onExport("json")} />
          <ExportButton label="HTML" onClick={() => onExport("html")} />
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="secondary-button !rounded-full !px-4 !py-2 text-rose-600 disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
            삭제
          </button>
        </div>
      </div>
    </div>
  );
}

function ExportButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="secondary-button !rounded-full !px-4 !py-2">
      <Download className="h-4 w-4" />
      {label}
    </button>
  );
}

function CenteredState({ icon, title, action }: { icon: ReactNode; title: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      {icon}
      <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">{title}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
