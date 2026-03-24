"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  CheckCircle2,
  Clock3,
  Eye,
  FileCode2,
  FileStack,
  FileText,
  FolderOpen,
  Loader2,
  Presentation,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";
import { api, type OutputDocument } from "@/lib/api";
import { AppShell, SectionHeader, formatDate } from "@/components/app-shell";
import { HeroOrbs } from "@/components/hero-orbs";
import { HeroIllustration } from "@/components/hero-illustration";

type DocTypeFilter = "all" | "PRD" | "TRD" | "WBS" | "Proposal" | "PPT";

const DOC_TYPE_META: Record<
  Exclude<DocTypeFilter, "all">,
  { label: string; shortLabel: string; icon: typeof FileText; note: string }
> = {
  PRD: { label: "제품 요구사항 문서", shortLabel: "PRD", icon: FileText, note: "핵심 요구사항과 범위" },
  TRD: { label: "기술 요구사항 문서", shortLabel: "TRD", icon: FileCode2, note: "기술 설계와 시스템 구성" },
  WBS: { label: "작업 분해 구조", shortLabel: "WBS", icon: FileCode2, note: "일정과 작업 실행 계획" },
  Proposal: { label: "제안서", shortLabel: "제안서", icon: FileStack, note: "외부 공유용 제안 문서" },
  PPT: { label: "발표 자료", shortLabel: "PPT", icon: Presentation, note: "발표용 결과 파일" },
};

const FILTERS: DocTypeFilter[] = ["all", "PRD", "TRD", "WBS", "Proposal", "PPT"];

function getViewerHref(doc: OutputDocument) {
  switch (doc.doc_type) {
    case "PRD":
      return `/prd/${doc.id}`;
    case "TRD":
      return `/doc/trd/${doc.id}`;
    case "WBS":
      return `/doc/wbs/${doc.id}`;
    case "Proposal":
      return `/doc/proposal/${doc.id}`;
    default:
      return null;
  }
}

export default function MainPage() {
  const [docFilter, setDocFilter] = useState<DocTypeFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: outputsData, isLoading, refetch, dataUpdatedAt } = useQuery({
    queryKey: ["output-documents"],
    queryFn: () => api.listOutputDocuments(),
    refetchInterval: 30000,
  });

  const outputs = useMemo(
    () => (Array.isArray(outputsData?.documents) ? outputsData.documents : []),
    [outputsData?.documents]
  );

  const filteredOutputs = useMemo(() => {
    const normalized = searchQuery.trim().toLowerCase();
    return outputs.filter((doc) => {
      const matchesType = docFilter === "all" || doc.doc_type === docFilter;
      const matchesSearch = !normalized || (doc.title ?? "").toLowerCase().includes(normalized);
      return matchesType && matchesSearch;
    });
  }, [docFilter, outputs, searchQuery]);

  const stats = useMemo(
    () => ({
      total: outputs.length,
      PRD: outputs.filter((doc) => doc.doc_type === "PRD").length,
      TRD: outputs.filter((doc) => doc.doc_type === "TRD").length,
      WBS: outputs.filter((doc) => doc.doc_type === "WBS").length,
      Proposal: outputs.filter((doc) => doc.doc_type === "Proposal").length,
      PPT: outputs.filter((doc) => doc.doc_type === "PPT").length,
    }),
    [outputs]
  );

  const recentDocuments = useMemo(() => outputs.slice(0, 3), [outputs]);

  return (
    <AppShell>
      <section className="section-card relative overflow-hidden">
        <HeroOrbs />
        {/* 데스크톱: 텍스트 col 우측 공간에 SVG 일러스트 배치 */}
        <HeroIllustration className="pointer-events-none absolute inset-y-0 left-[32%] right-[340px] my-auto hidden h-[220px] opacity-[0.55] xl:block" />
        <div className="relative z-10 grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
              D&apos;Maker
            </span>
            <h1 className="mt-5 max-w-[12ch] text-4xl font-semibold tracking-[-0.06em] text-slate-900">
              문서를 더 가볍고 세련되게 만듭니다
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
              문서 자동화를 통한 업무효율 향상
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/upload" className="brand-button">
                <Sparkles className="h-4 w-4" />
                새 문서 생성
              </Link>
              <button onClick={() => refetch()} className="secondary-button">
                <RefreshCw className="h-4 w-4" />
                새로고침
              </button>
            </div>

            <HeroIllustration className="mt-6 w-full max-w-[400px] opacity-80 xl:hidden" />
          </div>

          <aside className="surface-muted rounded-[30px] p-5">
            <p className="data-label">현재 보관 상태</p>
            <div className="mt-4 grid gap-3">
              <DashboardLine label="총 산출물" value={`${stats.total}개`} />
              <DashboardLine
                label="마지막 동기화"
                value={
                  dataUpdatedAt
                    ? formatDate(new Date(dataUpdatedAt).toISOString(), { hour: "2-digit", minute: "2-digit" })
                    : "-"
                }
              />
              <DashboardLine label="활성 필터" value={docFilter === "all" ? "전체" : docFilter} />
            </div>

            <div className="mt-5 border-t border-[var(--line-soft)] pt-4">
              <p className="text-sm font-semibold text-slate-900">최근 문서</p>
              <div className="mt-3 space-y-2">
                {recentDocuments.length ? (
                  recentDocuments.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between gap-3 text-sm">
                      <span className="truncate font-medium text-slate-800">{doc.title ?? ""}</span>
                      <span className="text-slate-500">{doc.doc_type ?? ""}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">아직 생성된 파일이 없습니다.</p>
                )}
              </div>
            </div>
          </aside>
        </div>

        <div className="relative z-10 mt-6 grid gap-3 md:grid-cols-3">
          <CompactSummary label="문서 타입" value={FILTERS.length - 1} note="현재 관리 중인 산출물 분류" />
          <CompactSummary label="최근 파일" value={recentDocuments.length} note="첫 화면에서 바로 이어지는 항목" accent="brand" />
          <CompactSummary label="검색 결과" value={filteredOutputs.length} note="현재 필터 기준 표시 수" accent="mint" />
        </div>
      </section>

      <section className="section-card">
        <SectionHeader title="생성 문서" description="검색과 타입 필터로 필요한 문서만 남기고 바로 상세 화면으로 이동합니다." />

        <div className="mb-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="문서 제목으로 검색"
              className="input-surface pl-11"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            {FILTERS.map((filter) => {
              const active = filter === docFilter;
              const meta = filter === "all" ? null : DOC_TYPE_META[filter];
              const count = filter === "all" ? stats.total : (stats[filter] ?? 0);

              return (
                <button
                  key={filter}
                  onClick={() => setDocFilter(filter)}
                  className={`tab-button ${active ? "tab-button-active" : "tab-button-idle"}`}
                >
                  {filter === "all" ? "전체" : meta?.shortLabel}
                  <span className={`rounded-full px-2 py-0.5 text-[11px] ${active ? "bg-white/15 text-white" : "bg-black/5 text-slate-500"}`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {isLoading ? (
          <LoadingState />
        ) : filteredOutputs.length === 0 ? (
          <EmptyState
            title={docFilter === "all" ? "아직 생성된 문서가 없습니다" : `${docFilter} 문서가 없습니다`}
            description="문서를 생성하면 이 화면에서 바로 확인하고 상세 화면으로 이어질 수 있습니다."
          />
        ) : (
          <div className="space-y-3">
            {filteredOutputs.map((doc) => (
              <DocumentRow key={doc.id} doc={doc} />
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}

function DashboardLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="font-semibold text-slate-900">{value}</span>
    </div>
  );
}

function CompactSummary({
  label,
  value,
  note,
  accent,
}: {
  label: string;
  value: string | number;
  note: string;
  accent?: "brand" | "mint";
}) {
  const accentClasses =
    accent === "brand"
      ? "border-[rgba(25,74,119,0.1)] bg-[rgba(25,74,119,0.06)]"
      : accent === "mint"
        ? "border-[rgba(15,118,110,0.1)] bg-[rgba(15,118,110,0.06)]"
        : "border-[var(--line-soft)] bg-[var(--bg-panel-muted)]";

  return (
    <div className={`rounded-[22px] border px-4 py-4 ${accentClasses}`}>
      <p className="data-label">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-slate-900">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{note}</p>
    </div>
  );
}

function DocumentRow({ doc }: { doc: OutputDocument }) {
  const meta = DOC_TYPE_META[doc.doc_type as keyof typeof DOC_TYPE_META] ?? DOC_TYPE_META.PRD;
  const viewerHref = getViewerHref(doc);
  const Icon = meta.icon;

  return (
    <div className="list-card">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] text-slate-700">
            <Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="pill-badge bg-slate-100 text-slate-700">{meta.shortLabel}</span>
              <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                <Clock3 className="h-3.5 w-3.5" />
                {formatDate(doc.created_at ?? undefined)}
              </span>
              <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
                <CheckCircle2 className="h-3.5 w-3.5" />
                완료
              </span>
            </div>
            <p className="mt-2 text-lg font-semibold tracking-[-0.03em] text-slate-900">{doc.title ?? ""}</p>
            <p className="mt-1 text-sm text-slate-500">{meta.note}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {viewerHref ? (
            <Link href={viewerHref} className="brand-button">
              <Eye className="h-4 w-4" />
              열기
            </Link>
          ) : null}
          {doc.has_pptx ? (
            <button
              onClick={async () => {
                try {
                  await api.openPptxFile(doc.id);
                } catch (error) {
                  console.error("PPTX 파일을 열지 못했습니다.", error);
                  alert("PPTX 파일을 열지 못했습니다.");
                }
              }}
              className="secondary-button"
            >
              <Presentation className="h-4 w-4" />
              PPTX
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
      <p className="mt-4 text-sm text-slate-500">문서를 불러오는 중입니다.</p>
    </div>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[1.4rem] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-6 py-20 text-center">
      <FolderOpen className="h-12 w-12 text-slate-400" />
      <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>
      <Link href="/upload" className="brand-button mt-6">
        <Sparkles className="h-4 w-4" />
        첫 문서 생성
      </Link>
    </div>
  );
}
