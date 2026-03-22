"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";
import {
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  Code2,
  FileCode2,
  FileJson2,
  FileStack,
  FileText,
  FolderOpen,
  LayoutDashboard,
  Loader2,
  Presentation,
  RefreshCw,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { api, type OutputDocument } from "@/lib/api";
import { AppShell, HeroPanel, MetricCard, SectionHeader, formatDate } from "@/components/app-shell";

type ViewerState = {
  isOpen: boolean;
  docId: string;
  docTitle: string;
  format: "json" | "md";
  content: string;
  loading: boolean;
};

type DocTypeFilter = "all" | "PRD" | "TRD" | "WBS" | "Proposal" | "PPT";

const DOC_TYPE_META: Record<
  Exclude<DocTypeFilter, "all">,
  { label: string; shortLabel: string; icon: typeof FileText; tone: string; note: string }
> = {
  PRD: { label: "제품 요구사항 문서", shortLabel: "PRD", icon: FileText, tone: "from-blue-700 to-sky-400", note: "서비스 방향과 요구사항 정의" },
  TRD: { label: "기술 요구사항 문서", shortLabel: "TRD", icon: FileCode2, tone: "from-indigo-700 to-blue-400", note: "구현 관점의 기술 설계" },
  WBS: { label: "작업 분해 구조", shortLabel: "WBS", icon: LayoutDashboard, tone: "from-emerald-700 to-teal-400", note: "실행 일정과 작업 구조" },
  Proposal: { label: "제안서", shortLabel: "제안서", icon: FileStack, tone: "from-orange-500 to-amber-300", note: "대외 공유용 문서" },
  PPT: { label: "발표 자료", shortLabel: "PPT", icon: Presentation, tone: "from-rose-600 to-orange-300", note: "프레젠테이션 산출물" },
};

const FILTERS: DocTypeFilter[] = ["all", "PRD", "TRD", "WBS", "Proposal", "PPT"];

export default function MainPage() {
  const [docFilter, setDocFilter] = useState<DocTypeFilter>("all");
  const [deleting, setDeleting] = useState(false);
  const [viewer, setViewer] = useState<ViewerState>({
    isOpen: false,
    docId: "",
    docTitle: "",
    format: "json",
    content: "",
    loading: false,
  });

  const { data: outputsData, isLoading, refetch, dataUpdatedAt } = useQuery({
    queryKey: ["output-documents"],
    queryFn: () => api.listOutputDocuments(),
    refetchInterval: 30000,
  });

  const outputs = useMemo(() => outputsData?.documents ?? [], [outputsData?.documents]);
  const filteredOutputs = useMemo(
    () => outputs.filter((doc) => docFilter === "all" || doc.doc_type === docFilter),
    [docFilter, outputs]
  );

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

  useEffect(() => {
    document.body.classList.toggle("modal-open", viewer.isOpen);
    return () => document.body.classList.remove("modal-open");
  }, [viewer.isOpen]);

  async function openContentViewer(doc: OutputDocument, format: "json" | "md") {
    setViewer({
      isOpen: true,
      docId: doc.id,
      docTitle: doc.title,
      format,
      content: "",
      loading: true,
    });

    try {
      const response = await api.getOutputDocument(doc.id, format);
      const content = format === "json" ? JSON.stringify(response.content_json ?? {}, null, 2) : response.content_md ?? "";
      setViewer((prev) => ({ ...prev, content, loading: false }));
    } catch (error) {
      console.error("문서 내용을 불러오지 못했습니다.", error);
      setViewer((prev) => ({ ...prev, content: "문서 내용을 불러오지 못했습니다.", loading: false }));
    }
  }

  async function handleDeleteAll() {
    if (!outputs.length) {
      alert("삭제할 생성 문서가 없습니다.");
      return;
    }

    const confirmed = confirm(`생성 문서 ${outputs.length}개를 모두 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`);
    if (!confirmed) return;

    setDeleting(true);
    try {
      const response = await api.deleteAllDocuments();
      alert(response.message);
      await refetch();
    } catch (error) {
      console.error("문서 삭제에 실패했습니다.", error);
      alert("문서 삭제에 실패했습니다.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <AppShell>
      <HeroPanel
        kicker="문서 스튜디오"
        title="생성된 산출물을 하나의 화면에서 선별하고 탐색합니다"
        description="결과 문서를 더 빠르게 훑고, 필요한 파일만 미리 본 뒤 바로 열 수 있도록 메인 대시보드를 다시 정리했습니다. 최근 산출물과 문서 타입 분포가 먼저 보이고, 아래에서는 아카이브를 바로 조작할 수 있습니다."
        actions={
          <>
            <Link href="/upload" className="brand-button">
              <Sparkles className="h-4 w-4" />
              새 문서 생성
            </Link>
            <button onClick={() => refetch()} className="secondary-button">
              <RefreshCw className="h-4 w-4" />
              새로고침
            </button>
          </>
        }
        aside={
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <p className="data-label">최근 동기화</p>
              <span className="pill-badge bg-emerald-100 text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse-soft" />
                실시간
              </span>
            </div>
            <p className="text-4xl font-black tracking-[-0.06em] text-slate-900">
              {formatDate(new Date(dataUpdatedAt || Date.now()).toISOString(), {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </p>
            <div className="grid gap-3">
              <div className="surface-muted p-4">
                <p className="data-label">문서 형식</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">JSON, Markdown, PPTX를 같은 흐름에서 확인하고 열 수 있습니다.</p>
              </div>
              <div className="surface-muted p-4">
                <p className="data-label">탐색 흐름</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">결과 확인, 미리보기, 삭제, 외부 열기까지 한 화면에서 이어집니다.</p>
              </div>
            </div>
          </div>
        }
      />

      <section className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="전체 산출물" value={stats.total} note="현재 저장된 생성 문서" />
          <MetricCard label="PRD" value={stats.PRD} note="제품 요구사항 문서" accent="brand" />
          <MetricCard label="TRD" value={stats.TRD} note="기술 설계 문서" accent="brand" />
          <MetricCard label="WBS" value={stats.WBS} note="실행 계획 구조" accent="mint" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="section-card stagger-in">
            <p className="data-label">빠른 작업</p>
            <div className="mt-4 space-y-3">
              <QuickLink href="/upload" title="입력 파일 등록" description="원본 문서를 올리고 생성 파이프라인을 시작합니다." />
              <QuickLink href="/history" title="PRD 아카이브 열기" description="기존 PRD를 다시 확인하고 내보낼 수 있습니다." />
            </div>
          </div>
          <div className="section-card stagger-in">
            <p className="data-label">문서 타입 맵</p>
            <div className="mt-4 space-y-3">
              {(["PRD", "TRD", "WBS", "Proposal", "PPT"] as const).map((type) => {
                const meta = DOC_TYPE_META[type];
                const count = stats[type];
                return (
                  <div key={type} className="surface-muted flex items-center justify-between px-4 py-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{meta.label}</p>
                      <p className="text-xs text-slate-500">{meta.note}</p>
                    </div>
                    <span className="text-xl font-black tracking-[-0.05em] text-slate-900">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="section-card">
          <SectionHeader
            title="생성 문서 아카이브"
            description="문서 타입별로 필터링하고, 세부 내용을 바로 열람할 수 있습니다."
            action={
              <button
                onClick={handleDeleteAll}
                disabled={deleting || outputs.length === 0}
                className="secondary-button !rounded-full !px-4 !py-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                전체 삭제
              </button>
            }
          />

          <div className="mb-5 flex flex-wrap gap-2">
            {FILTERS.map((filter) => {
              const active = filter === docFilter;
              const meta = filter === "all" ? null : DOC_TYPE_META[filter];
              const Icon = meta?.icon ?? FolderOpen;
              const count = filter === "all" ? stats.total : stats[filter];

              return (
                <button key={filter} onClick={() => setDocFilter(filter)} className={`tab-button ${active ? "tab-button-active" : "tab-button-idle"}`}>
                  <Icon className="h-4 w-4" />
                  {filter === "all" ? "전체" : meta?.shortLabel}
                  <span className={`rounded-full px-2 py-0.5 text-xs ${active ? "bg-white/20 text-white" : "bg-slate-100 text-slate-500"}`}>{count}</span>
                </button>
              );
            })}
          </div>

          {isLoading ? (
            <LoadingState />
          ) : filteredOutputs.length === 0 ? (
            <EmptyState
              title={docFilter === "all" ? "아직 생성된 문서가 없습니다" : `${docFilter} 문서가 없습니다`}
              description="문서 생성 작업을 실행하면 결과물이 이곳에 쌓입니다."
            />
          ) : (
            <div className="space-y-3">
              {filteredOutputs.map((doc, index) => (
                <DocumentRow key={doc.id} doc={doc} onViewContent={openContentViewer} priority={index < 2} />
              ))}
            </div>
          )}
        </div>

        <aside className="section-card stagger-in">
          <SectionHeader title="작업 힌트" description="대시보드에서 바로 이어서 처리할 수 있는 흐름입니다." />
          <div className="space-y-4">
            <div className="surface-muted p-4">
              <p className="data-label">미리보기</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">JSON과 Markdown은 모달에서 바로 열어 구조를 빠르게 확인할 수 있습니다.</p>
            </div>
            <div className="surface-muted p-4">
              <p className="data-label">프레젠테이션</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">PPTX 결과물은 외부 프로그램으로 곧바로 열 수 있도록 연결했습니다.</p>
            </div>
            <div className="surface-muted p-4">
              <p className="data-label">정리 작업</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">문서가 쌓이면 전체 삭제로 아카이브를 한 번에 정리할 수 있습니다.</p>
            </div>
          </div>
        </aside>
      </section>

      {viewer.isOpen ? (
        <ContentViewerModal
          viewer={viewer}
          onClose={() =>
            setViewer({
              isOpen: false,
              docId: "",
              docTitle: "",
              format: "json",
              content: "",
              loading: false,
            })
          }
        />
      ) : null}
    </AppShell>
  );
}

function QuickLink({ href, title, description }: { href: string; title: string; description: string }) {
  return (
    <Link href={href} className="list-card block">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-base font-semibold text-slate-900">{title}</p>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>
        <ArrowUpRight className="h-5 w-5 text-slate-400" />
      </div>
    </Link>
  );
}

function DocumentRow({
  doc,
  onViewContent,
  priority,
}: {
  doc: OutputDocument;
  onViewContent: (doc: OutputDocument, format: "json" | "md") => void;
  priority?: boolean;
}) {
  const meta = DOC_TYPE_META[doc.doc_type as keyof typeof DOC_TYPE_META] ?? DOC_TYPE_META.PRD;
  const Icon = meta.icon;

  return (
    <div className={`list-card ${priority ? "ring-1 ring-blue-200/70" : ""}`}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-[22px] bg-gradient-to-br ${meta.tone} text-white shadow-sm`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="pill-badge bg-slate-100 text-slate-700">{meta.label}</span>
              {priority ? <span className="pill-badge bg-blue-100 text-blue-700">최근 생성</span> : null}
            </div>
            <p className="mt-3 truncate text-xl font-bold tracking-[-0.04em] text-slate-900">{doc.title}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-500">
              <span className="inline-flex items-center gap-1">
                <Clock3 className="h-4 w-4" />
                {formatDate(doc.created_at)}
              </span>
              <span className="inline-flex items-center gap-1 text-emerald-700">
                <CheckCircle2 className="h-4 w-4" />
                생성 완료
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {doc.has_json ? (
            <button onClick={() => onViewContent(doc, "json")} className="secondary-button !rounded-full !px-4 !py-2">
              <FileJson2 className="h-4 w-4" />
              JSON
            </button>
          ) : null}
          {doc.has_md ? (
            <button onClick={() => onViewContent(doc, "md")} className="secondary-button !rounded-full !px-4 !py-2">
              <Code2 className="h-4 w-4" />
              마크다운
            </button>
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
              className="brand-button !rounded-full !px-4 !py-2"
            >
              <Presentation className="h-4 w-4" />
              PPTX 열기
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
    <div className="surface-muted flex flex-col items-center justify-center rounded-[28px] px-6 py-24 text-center">
      <FolderOpen className="h-12 w-12 text-slate-300" />
      <p className="mt-4 text-xl font-semibold tracking-tight text-slate-800">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}

function ContentViewerModal({ viewer, onClose }: { viewer: ViewerState; onClose: () => void }) {
  let parsedJson: unknown = {};
  if (viewer.format === "json" && viewer.content) {
    try {
      parsedJson = JSON.parse(viewer.content);
    } catch {
      parsedJson = { error: viewer.content };
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8">
      <button className="absolute inset-0 bg-slate-900/35 backdrop-blur-sm" onClick={onClose} aria-label="모달 닫기" />
      <div className="glass-panel-strong relative z-10 flex max-h-[88vh] w-full max-w-6xl flex-col overflow-hidden rounded-[32px]">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div className="min-w-0">
            <p className="truncate text-lg font-semibold text-slate-900">{viewer.docTitle}</p>
            <p className="mt-1 text-sm text-slate-500">{viewer.format.toUpperCase()} 미리보기</p>
          </div>
          <button onClick={onClose} className="secondary-button !rounded-full !px-4 !py-2">
            <X className="h-4 w-4" />
            닫기
          </button>
        </div>
        <div className="overflow-auto p-6">
          {viewer.loading ? (
            <div className="flex items-center justify-center py-24">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : viewer.format === "md" ? (
            <div className="prose-modern">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{viewer.content}</ReactMarkdown>
            </div>
          ) : (
            <div className="surface-muted overflow-x-auto rounded-[28px] p-5">
              <JsonViewer data={parsedJson} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function JsonViewer({ data }: { data: unknown }) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  function toggleCollapse(key: string) {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function renderValue(value: unknown, key: string): React.ReactNode {
    const palette = {
      null: "text-slate-400",
      boolean: "text-amber-700",
      number: "text-sky-700",
      string: "text-emerald-700",
      property: "text-blue-700",
      bracket: "text-slate-500",
    };

    if (value === null) return <span className={palette.null}>null</span>;
    if (typeof value === "boolean") return <span className={palette.boolean}>{String(value)}</span>;
    if (typeof value === "number") return <span className={palette.number}>{value}</span>;
    if (typeof value === "string") return <span className={palette.string}>&quot;{value}&quot;</span>;

    if (Array.isArray(value)) {
      if (!value.length) return <span className={palette.bracket}>[]</span>;
      const isCollapsed = collapsed[key];
      return (
        <div className="inline">
          <button onClick={() => toggleCollapse(key)} className="mr-1 text-slate-500 hover:text-slate-900">
            {isCollapsed ? ">" : "v"}
          </button>
          <span className={palette.bracket}>[</span>
          <span className="ml-1 text-xs text-slate-400">{value.length}개 항목</span>
          {!isCollapsed ? (
            <div className="ml-4 border-l border-slate-200 pl-3">
              {value.map((item, index) => (
                <div key={`${key}-${index}`} className="my-1">
                  {renderValue(item, `${key}-${index}`)}
                  {index < value.length - 1 ? <span className={palette.bracket}>,</span> : null}
                </div>
              ))}
            </div>
          ) : null}
          <span className={palette.bracket}>]</span>
        </div>
      );
    }

    if (typeof value === "object") {
      const entries = Object.entries(value as Record<string, unknown>);
      if (!entries.length) return <span className={palette.bracket}>{"{}"}</span>;
      const isCollapsed = collapsed[key];
      return (
        <div className="inline">
          <button onClick={() => toggleCollapse(key)} className="mr-1 text-slate-500 hover:text-slate-900">
            {isCollapsed ? ">" : "v"}
          </button>
          <span className={palette.bracket}>{"{"}</span>
          <span className="ml-1 text-xs text-slate-400">{entries.length}개 필드</span>
          {!isCollapsed ? (
            <div className="ml-4 border-l border-slate-200 pl-3">
              {entries.map(([entryKey, entryValue], index) => (
                <div key={`${key}-${entryKey}`} className="my-1">
                  <span className={palette.property}>&quot;{entryKey}&quot;</span>
                  <span className={palette.bracket}>: </span>
                  {renderValue(entryValue, `${key}-${entryKey}`)}
                  {index < entries.length - 1 ? <span className={palette.bracket}>,</span> : null}
                </div>
              ))}
            </div>
          ) : null}
          <span className={palette.bracket}>{"}"}</span>
        </div>
      );
    }

    return <span className={palette.null}>{String(value)}</span>;
  }

  return <div className="font-mono text-sm leading-7">{renderValue(data, "root")}</div>;
}
