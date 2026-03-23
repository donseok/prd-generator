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
import { api, type Project, type ProjectSummary } from "@/lib/api";
import { AppShell, SectionHeader, formatDate } from "@/components/app-shell";

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
  archived: { label: "보관", className: "bg-slate-100 text-slate-600" },
};

const DOC_TYPE_META: Record<string, { label: string; icon: typeof FileText; dotColor: string }> = {
  PRD: { label: "PRD", icon: FileText, dotColor: "bg-sky-600" },
  TRD: { label: "TRD", icon: FileCode2, dotColor: "bg-cyan-600" },
  WBS: { label: "WBS", icon: LayoutDashboard, dotColor: "bg-emerald-600" },
  Proposal: { label: "제안서", icon: FileStack, dotColor: "bg-amber-600" },
  PPT: { label: "PPT", icon: Presentation, dotColor: "bg-rose-600" },
};

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);

  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formTags, setFormTags] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.listProjects(0, 100),
    refetchInterval: 30000,
  });

  const projects = useMemo(() => data?.projects ?? [], [data?.projects]);

  const filteredProjects = useMemo(() => {
    let result = projects;

    if (statusFilter !== "all") {
      result = result.filter((project) => project.status === statusFilter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter(
        (project) =>
          project.name.toLowerCase().includes(q) ||
          (project.description ?? "").toLowerCase().includes(q) ||
          (project.tags ?? []).some((tag) => tag.toLowerCase().includes(q))
      );
    }

    return result;
  }, [projects, searchQuery, statusFilter]);

  const createMutation = useMutation({
    mutationFn: () => {
      const tags = formTags
        .split(",")
        .map((value) => value.trim())
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

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!formName.trim()) return;
    createMutation.mutate();
  }

  function statusCount(key: StatusFilter) {
    if (key === "all") return projects.length;
    return projects.filter((project) => project.status === key).length;
  }

  return (
    <AppShell>
      <section className="section-card">
        <span className="inline-flex items-center gap-2 rounded-full border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
          Project Index
        </span>
        <h1 className="mt-5 max-w-[12ch] text-4xl font-semibold tracking-[-0.06em] text-slate-900">
          프로젝트를 더 선명한 구조로 정리합니다
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
          프로젝트 화면은 생성과 탐색에만 집중합니다. 상태 요약보다는 검색, 필터, 카드 목록이 먼저 보이도록 화면을 더 가볍게 비웠습니다.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button onClick={() => setShowCreateForm((prev) => !prev)} className="brand-button">
            <Plus className="h-4 w-4" />
            새 프로젝트
          </button>
        </div>
      </section>

      {showCreateForm ? (
        <section className="section-card">
          <SectionHeader title="새 프로젝트 생성" description="필수 정보만 입력하면 바로 생성됩니다." />
          <form onSubmit={handleCreate} className="grid gap-4">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="grid gap-2">
                <span className="data-label">프로젝트 이름</span>
                <input
                  type="text"
                  value={formName}
                  onChange={(event) => setFormName(event.target.value)}
                  placeholder="프로젝트 이름을 입력하세요"
                  required
                  className="input-surface"
                />
              </label>
              <label className="grid gap-2">
                <span className="data-label">태그</span>
                <input
                  type="text"
                  value={formTags}
                  onChange={(event) => setFormTags(event.target.value)}
                  placeholder="쉼표로 구분 (예: 웹앱, MVP)"
                  className="input-surface"
                />
              </label>
            </div>

            <label className="grid gap-2">
              <span className="data-label">설명</span>
              <textarea
                value={formDescription}
                onChange={(event) => setFormDescription(event.target.value)}
                placeholder="프로젝트에 대한 간단한 설명"
                rows={3}
                className="input-surface"
              />
            </label>

            <div className="flex flex-wrap items-center gap-3">
              <button type="submit" disabled={!formName.trim() || createMutation.isPending} className="brand-button disabled:cursor-not-allowed disabled:opacity-50">
                {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
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
              {createMutation.isError ? <span className="text-sm text-orange-700">프로젝트 생성에 실패했습니다.</span> : null}
            </div>
          </form>
        </section>
      ) : null}

      <section className="section-card">
        <SectionHeader title="프로젝트 목록" description="검색과 상태 필터를 먼저 두고, 프로젝트 카드를 바로 탐색할 수 있게 정리했습니다." />

        <div className="mb-5 grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="프로젝트 이름, 설명, 태그로 검색"
              className="input-surface pl-11"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            {STATUS_TABS.map(({ key, label }) => {
              const active = key === statusFilter;
              return (
                <button key={key} onClick={() => setStatusFilter(key)} className={`tab-button ${active ? "tab-button-active" : "tab-button-idle"}`}>
                  {label}
                  <span className={`rounded-full px-2 py-0.5 text-[11px] ${active ? "bg-white/15 text-white" : "bg-black/5 text-slate-500"}`}>
                    {statusCount(key)}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {isLoading ? (
          <LoadingState />
        ) : filteredProjects.length === 0 ? (
          <EmptyState
            title={searchQuery ? "검색 결과가 없습니다" : "프로젝트가 없습니다"}
            description={searchQuery ? "다른 검색어나 상태 필터를 시도해 보세요." : "새 프로젝트를 만들어 문서를 구조적으로 관리하세요."}
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

function ProjectCard({ project }: { project: ProjectSummary }) {
  const badge = STATUS_BADGE[project.status] ?? STATUS_BADGE.active;
  const documentCount = project.document_count ?? 0;

  return (
    <Link href={`/projects/${project.id}`} className="list-card group block">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <FolderKanban className="h-5 w-5 shrink-0 text-slate-700" />
              <h3 className="truncate text-lg font-semibold tracking-[-0.03em] text-slate-900">{project.name}</h3>
            </div>
            {project.description ? <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">{project.description}</p> : null}
          </div>
          <span className={`pill-badge shrink-0 ${badge.className}`}>{badge.label}</span>
        </div>

        {documentCount > 0 ? (
          <p className="text-sm text-slate-600">문서 {documentCount}개 연결됨</p>
        ) : (
          <p className="text-sm text-slate-500">연결된 문서가 없습니다.</p>
        )}

        {(project.tags ?? []).length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {(project.tags ?? []).map((tag) => (
              <span key={tag} className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                <Tag className="h-3 w-3" />
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Clock3 className="h-3.5 w-3.5" />
          {formatDate(project.created_at, {
            year: "numeric",
            month: "short",
            day: "numeric",
          })}
        </div>
      </div>
    </Link>
  );
}

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
    <div className="flex flex-col items-center justify-center rounded-[1.4rem] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-6 py-20 text-center">
      <FolderOpen className="h-12 w-12 text-slate-400" />
      <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}
