"use client";

import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Clock3,
  FileCode2,
  FileStack,
  FileText,
  FolderKanban,
  FolderOpen,
  LayoutDashboard,
  Loader2,
  Plus,
  Presentation,
  Search,
  Tag,
  X,
} from "lucide-react";
import { api, type Project } from "@/lib/api";
import { AppShell, HeroPanel, MetricCard, SectionHeader, formatDate } from "@/components/app-shell";

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

type StatusFilter = "all" | "active" | "completed" | "archived";

const STATUS_TABS: { key: StatusFilter; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "active", label: "활성" },
  { key: "completed", label: "완료" },
  { key: "archived", label: "보관" },
];

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  active: { label: "활성", className: "bg-emerald-100 text-emerald-700" },
  completed: { label: "완료", className: "bg-blue-100 text-blue-700" },
  archived: { label: "보관", className: "bg-slate-100 text-slate-500" },
};

const DOC_TYPE_META: Record<string, { label: string; icon: typeof FileText; dotColor: string }> = {
  PRD: { label: "PRD", icon: FileText, dotColor: "bg-blue-500" },
  TRD: { label: "TRD", icon: FileCode2, dotColor: "bg-purple-500" },
  WBS: { label: "WBS", icon: LayoutDashboard, dotColor: "bg-emerald-500" },
  Proposal: { label: "제안서", icon: FileStack, dotColor: "bg-orange-500" },
  PPT: { label: "PPT", icon: Presentation, dotColor: "bg-rose-500" },
};

/* -------------------------------------------------------------------------- */
/*  Main Page                                                                  */
/* -------------------------------------------------------------------------- */

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);

  /* -- Create form state -- */
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formTags, setFormTags] = useState("");

  /* -- Data fetching -- */
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.listProjects(0, 100),
    refetchInterval: 30000,
  });

  const projects = useMemo(() => data?.projects ?? [], [data?.projects]);

  /* -- Filtering -- */
  const filteredProjects = useMemo(() => {
    let result = projects;

    if (statusFilter !== "all") {
      result = result.filter((p) => p.status === statusFilter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    return result;
  }, [projects, statusFilter, searchQuery]);

  /* -- Stats -- */
  const stats = useMemo(
    () => ({
      total: projects.length,
      active: projects.filter((p) => p.status === "active").length,
      completed: projects.filter((p) => p.status === "completed").length,
      archived: projects.filter((p) => p.status === "archived").length,
    }),
    [projects]
  );

  /* -- Create mutation -- */
  const createMutation = useMutation({
    mutationFn: () => {
      const tags = formTags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      return api.createProject(formName.trim(), formDescription.trim(), tags);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowCreateForm(false);
      setFormName("");
      setFormDescription("");
      setFormTags("");
    },
  });

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim()) return;
    createMutation.mutate();
  }

  function statusCount(key: StatusFilter): number {
    if (key === "all") return projects.length;
    return projects.filter((p) => p.status === key).length;
  }

  return (
    <AppShell>
      {/* Hero */}
      <HeroPanel
        kicker="프로젝트"
        title="프로젝트 관리"
        description="여러 프로젝트를 개별 워크스페이스로 분리하여 문서를 체계적으로 관리합니다. 각 프로젝트 안에서 PRD, TRD, WBS, 제안서, PPT를 한 곳에서 추적할 수 있습니다."
        actions={
          <>
            <button
              onClick={() => setShowCreateForm((prev) => !prev)}
              className="brand-button"
            >
              <Plus className="h-4 w-4" />
              새 프로젝트
            </button>
            <Link href="/" className="secondary-button">
              <FolderKanban className="h-4 w-4" />
              대시보드
            </Link>
          </>
        }
      />

      {/* Metrics */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="전체 프로젝트" value={stats.total} note="등록된 프로젝트" />
        <MetricCard label="활성" value={stats.active} note="진행 중인 프로젝트" accent="brand" />
        <MetricCard label="완료" value={stats.completed} note="완료된 프로젝트" accent="mint" />
        <MetricCard label="보관" value={stats.archived} note="보관된 프로젝트" accent="warm" />
      </section>

      {/* Inline Creation Form */}
      {showCreateForm ? (
        <section className="section-card">
          <SectionHeader title="새 프로젝트 생성" description="프로젝트 기본 정보를 입력합니다." />
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="data-label mb-1.5 block">프로젝트 이름 *</label>
              <input
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="프로젝트 이름을 입력하세요"
                required
                className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 placeholder:text-[var(--text-muted)] focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
              />
            </div>
            <div>
              <label className="data-label mb-1.5 block">설명</label>
              <textarea
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                placeholder="프로젝트에 대한 간단한 설명"
                rows={3}
                className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 placeholder:text-[var(--text-muted)] focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
              />
            </div>
            <div>
              <label className="data-label mb-1.5 block">태그</label>
              <input
                type="text"
                value={formTags}
                onChange={(e) => setFormTags(e.target.value)}
                placeholder="쉼표로 구분 (예: 웹앱, 모바일, MVP)"
                className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 placeholder:text-[var(--text-muted)] focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
              />
            </div>
            <div className="flex items-center gap-3 pt-2">
              <button
                type="submit"
                disabled={!formName.trim() || createMutation.isPending}
                className="brand-button disabled:cursor-not-allowed disabled:opacity-50"
              >
                {createMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                생성
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setFormName("");
                  setFormDescription("");
                  setFormTags("");
                }}
                className="secondary-button"
              >
                <X className="h-4 w-4" />
                취소
              </button>
              {createMutation.isError ? (
                <span className="text-sm text-[#E03E3E]">프로젝트 생성에 실패했습니다.</span>
              ) : null}
            </div>
          </form>
        </section>
      ) : null}

      {/* Project List */}
      <section className="section-card">
        <SectionHeader
          title="프로젝트 목록"
          description="프로젝트를 검색하고 상태별로 필터링합니다."
        />

        {/* Search bar */}
        <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="프로젝트 이름, 설명, 태그로 검색"
              className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] py-3 pl-10 pr-4 text-sm text-slate-900 placeholder:text-[var(--text-muted)] focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
            />
          </div>
        </div>

        {/* Status filter tabs */}
        <div className="mb-5 flex flex-wrap gap-2">
          {STATUS_TABS.map(({ key, label }) => {
            const active = key === statusFilter;
            const count = statusCount(key);
            return (
              <button
                key={key}
                onClick={() => setStatusFilter(key)}
                className={`tab-button ${active ? "tab-button-active" : "tab-button-idle"}`}
              >
                {key === "all" ? <FolderOpen className="h-4 w-4" /> : <FolderKanban className="h-4 w-4" />}
                {label}
                <span
                  className={`rounded px-1.5 py-0.5 text-xs ${
                    active
                      ? "bg-white/25 text-white"
                      : "bg-[var(--bg-panel-muted)] text-[var(--text-muted)]"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Project cards */}
        {isLoading ? (
          <LoadingState />
        ) : filteredProjects.length === 0 ? (
          <EmptyState
            title={searchQuery ? "검색 결과가 없습니다" : "프로젝트가 없습니다"}
            description={
              searchQuery
                ? "다른 검색어를 사용하거나 필터를 조정해 보세요."
                : "새 프로젝트를 만들어 문서를 체계적으로 관리하세요."
            }
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}

/* -------------------------------------------------------------------------- */
/*  Project Card                                                               */
/* -------------------------------------------------------------------------- */

function ProjectCard({ project }: { project: Project }) {
  const badge = STATUS_BADGE[project.status] ?? STATUS_BADGE.active;

  const docCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const doc of project.documents) {
      counts[doc.doc_type] = (counts[doc.doc_type] || 0) + 1;
    }
    return counts;
  }, [project.documents]);

  return (
    <Link href={`/projects/${project.id}`} className="list-card group block transition-shadow hover:shadow-[var(--shadow-card-hover)]">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <FolderKanban className="h-5 w-5 shrink-0 text-[#2383E2]" />
              <h3 className="truncate text-lg font-bold tracking-[-0.03em] text-slate-900">
                {project.name}
              </h3>
            </div>
            {project.description ? (
              <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">
                {project.description}
              </p>
            ) : null}
          </div>
          <span className={`pill-badge shrink-0 ${badge.className}`}>{badge.label}</span>
        </div>

        {/* Document counts */}
        {project.documents.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {Object.entries(docCounts).map(([type, count]) => {
              const meta = DOC_TYPE_META[type];
              if (!meta) return null;
              return (
                <span key={type} className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--bg-panel-muted)] px-2.5 py-1 text-xs font-medium text-slate-600">
                  <span className={`h-1.5 w-1.5 rounded-full ${meta.dotColor}`} />
                  {meta.label} {count}
                </span>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-[var(--text-muted)]">연결된 문서가 없습니다</p>
        )}

        {/* Tags */}
        {project.tags.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {project.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-500"
              >
                <Tag className="h-3 w-3" />
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        {/* Footer */}
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="inline-flex items-center gap-1">
            <Clock3 className="h-3.5 w-3.5" />
            {formatDate(project.created_at, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
          <span>|</span>
          <span>문서 {project.documents.length}건</span>
        </div>
      </div>
    </Link>
  );
}

/* -------------------------------------------------------------------------- */
/*  Loading / Empty States                                                     */
/* -------------------------------------------------------------------------- */

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
      <p className="mt-4 text-sm text-slate-500">프로젝트를 불러오는 중입니다.</p>
    </div>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl bg-gradient-to-b from-[var(--bg-panel-muted)] to-[var(--bg-panel)] border border-[var(--line-soft)] px-6 py-24 text-center">
      <FolderOpen className="h-14 w-14 text-[#9B9A97]" />
      <p className="mt-4 text-xl font-semibold tracking-tight text-slate-800">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}
