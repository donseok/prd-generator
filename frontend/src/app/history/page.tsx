"use client";

import { useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Download, FileSearch, Loader2, Plus, Search, Trash2 } from "lucide-react";
import { api, type PRDListItem } from "@/lib/api";
import { AppShell, SectionHeader, TopBar, formatDate, scoreBadge } from "@/components/app-shell";

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

  const prds = useMemo(() => (Array.isArray(data?.prds) ? data.prds : []), [data?.prds]);
  const totalCount = data?.total ?? 0;
  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

  const filteredPrds = useMemo(() => {
    if (!searchQuery) return prds;
    return prds.filter((prd) => (prd.title ?? "").toLowerCase().includes(searchQuery.toLowerCase()));
  }, [prds, searchQuery]);

  async function handleExport(id: string) {
    try {
      const content = await api.exportPRD(id, "markdown");
      // api.exportPRD returns a Blob (responseType: "blob")
      const text = content instanceof Blob ? await content.text() : (typeof content === "string" ? content : JSON.stringify(content, null, 2));
      const blob = new Blob([text], {
        type: "text/plain",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `prd-${id}.md`;
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
      <section className="section-card">
        <SectionHeader
          title="문서 목록"
          description="저장된 PRD를 검색하고 다시 열거나 마크다운으로 내보낼 수 있습니다."
          action={
            totalPages > 0 ? (
              <span className="pill-badge bg-slate-100 text-slate-700">
                {page + 1} / {totalPages}
              </span>
            ) : null
          }
        />

        <div className="mb-6 grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="문서 제목 검색"
              className="input-surface pl-11"
            />
          </label>
        </div>

        {isLoading ? (
          <CenteredState icon={<Loader2 className="h-10 w-10 animate-spin text-slate-400" />} title="문서 목록을 불러오는 중입니다" />
        ) : error ? (
          <CenteredState icon={<FileSearch className="h-10 w-10 text-orange-500" />} title="문서 목록을 불러오지 못했습니다" />
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
              {filteredPrds.map((prd) => (
                <PRDCard
                  key={prd.id}
                  prd={prd}
                  onDelete={() => handleDelete(prd.id, prd.title)}
                  onExport={() => handleExport(prd.id)}
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
                <span className="text-sm font-semibold text-slate-700">
                  {page + 1} <span className="font-medium text-slate-400">/ {totalPages}</span>
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
    </AppShell>
  );
}

function CenteredState({ icon, title, action }: { icon: ReactNode; title: string; action?: ReactNode }) {
  return (
    <div className="flex min-h-[320px] flex-col items-center justify-center rounded-[1.4rem] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-6 py-12 text-center">
      {icon}
      <p className="mt-4 text-lg font-semibold tracking-tight text-slate-900">{title}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}

function PRDCard({
  prd,
  onDelete,
  onExport,
  isDeleting,
}: {
  prd: PRDListItem;
  onDelete: () => void;
  onExport: () => void;
  isDeleting: boolean;
}) {
  const badge = scoreBadge(prd.overall_confidence ?? 0);
  const statusStr = typeof prd.status === "string" ? prd.status : String(prd.status ?? "");
  const titleStr = typeof prd.title === "string" ? prd.title : String(prd.title ?? "");

  return (
    <div className="list-card">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`pill-badge ${badge.className}`}>{badge.label}</span>
            <span className="pill-badge bg-slate-100 text-slate-700">{STATUS_LABELS[statusStr] ?? statusStr}</span>
            <span className="text-xs text-slate-500">{formatDate(prd.created_at ?? "")}</span>
          </div>
          <p className="mt-2 text-lg font-semibold tracking-[-0.03em] text-slate-900">{titleStr}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link href={`/prd/${prd.id}`} className="brand-button">
            열기
          </Link>
          <button onClick={onExport} className="secondary-button">
            <Download className="h-4 w-4" />
            MD
          </button>
          <button onClick={onDelete} disabled={isDeleting} className="secondary-button disabled:cursor-not-allowed disabled:opacity-50">
            {isDeleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4 text-orange-600" />}
            삭제
          </button>
        </div>
      </div>
    </div>
  );
}
