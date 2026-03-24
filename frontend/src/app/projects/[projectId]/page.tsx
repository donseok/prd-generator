"use client";

import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FileCode2,
  FileStack,
  FileText,
  FolderKanban,
  FolderOpen,
  LayoutDashboard,
  Link2,
  Loader2,
  Presentation,
  Settings,
  Trash2,
  X,
} from "lucide-react";
import { api, type DocumentReference } from "@/lib/api";
import { AppShell, TopBar, SectionHeader, formatDate } from "@/components/app-shell";

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const DOC_TYPE_META: Record<
  string,
  {
    label: string;
    shortLabel: string;
    icon: typeof FileText;
    note: string;
    dotColor: string;
  }
> = {
  PRD: {
    label: "제품 요구사항 문서",
    shortLabel: "PRD",
    icon: FileText,
    note: "서비스 방향과 요구사항 정의",
    dotColor: "bg-sky-600",
  },
  TRD: {
    label: "기술 요구사항 문서",
    shortLabel: "TRD",
    icon: FileCode2,
    note: "구현 관점의 기술 설계",
    dotColor: "bg-cyan-600",
  },
  WBS: {
    label: "작업 분해 구조",
    shortLabel: "WBS",
    icon: LayoutDashboard,
    note: "실행 일정과 작업 구조",
    dotColor: "bg-emerald-600",
  },
  Proposal: {
    label: "제안서",
    shortLabel: "제안서",
    icon: FileStack,
    note: "대외 공유용 문서",
    dotColor: "bg-amber-600",
  },
  PPT: {
    label: "발표 자료",
    shortLabel: "PPT",
    icon: Presentation,
    note: "프레젠테이션 산출물",
    dotColor: "bg-rose-600",
  },
};

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  active: { label: "활성", className: "bg-emerald-100 text-emerald-700" },
  completed: { label: "완료", className: "bg-blue-100 text-blue-700" },
  archived: { label: "보관", className: "bg-slate-100 text-slate-500" },
};

const STATUS_OPTIONS = [
  { value: "active", label: "활성" },
  { value: "completed", label: "완료" },
  { value: "archived", label: "보관" },
];

function getDocViewerPath(docType: string, docId: string): string | null {
  switch (docType) {
    case "PRD":
      return `/prd/${docId}`;
    case "TRD":
      return `/doc/trd/${docId}`;
    case "WBS":
      return `/doc/wbs/${docId}`;
    case "Proposal":
      return `/doc/proposal/${docId}`;
    default:
      return null;
  }
}

/* -------------------------------------------------------------------------- */
/*  Main Page                                                                  */
/* -------------------------------------------------------------------------- */

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const projectId = params.projectId as string;

  const [showSettings, setShowSettings] = useState(false);
  const [showLinkDoc, setShowLinkDoc] = useState(false);

  /* -- Fetch project -- */
  const {
    data: project,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    enabled: !!projectId,
  });

  /* -- Fetch project documents -- */
  const { data: projectDocs } = useQuery({
    queryKey: ["project-documents", projectId],
    queryFn: () => api.getProjectDocuments(projectId),
    enabled: !!projectId,
  });

  /* -- Stats -- */
  const docs = useMemo(() => project?.documents ?? [], [project?.documents]);
  const stats = useMemo(() => {
    const counts: Record<string, number> = { total: docs.length };
    for (const doc of docs) {
      counts[doc.doc_type] = (counts[doc.doc_type] || 0) + 1;
    }
    return counts;
  }, [docs]);

  /* -- Group documents by type -- */
  const groupedDocs = useMemo(() => {
    const groups: Record<string, DocumentReference[]> = {};
    for (const doc of docs) {
      if (!groups[doc.doc_type]) groups[doc.doc_type] = [];
      groups[doc.doc_type].push(doc);
    }
    return groups;
  }, [docs]);

  /* -- Delete project mutation -- */
  const deleteMutation = useMutation({
    mutationFn: () => api.deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      router.push("/projects");
    },
  });

  /* -- Remove document mutation -- */
  const removeDocMutation = useMutation({
    mutationFn: (docId: string) => api.removeDocumentFromProject(projectId, docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project-documents", projectId] });
    },
  });

  function handleDeleteProject() {
    const confirmed = confirm("이 프로젝트를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.");
    if (!confirmed) return;
    deleteMutation.mutate();
  }

  if (isLoading) {
    return (
      <AppShell
        header={
          <TopBar title="프로젝트 로딩 중..." href="/projects" />
        }
      >
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
          <p className="mt-4 text-sm text-slate-500">프로젝트 정보를 불러오는 중입니다.</p>
        </div>
      </AppShell>
    );
  }

  if (isError || !project) {
    return (
      <AppShell
        header={
          <TopBar title="프로젝트를 찾을 수 없습니다" href="/projects" />
        }
      >
        <div className="flex flex-col items-center justify-center rounded-[1.4rem] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-6 py-24 text-center">
          <FolderOpen className="h-14 w-14 text-slate-400" />
          <p className="mt-4 text-xl font-semibold tracking-tight text-slate-800">
            프로젝트를 찾을 수 없습니다
          </p>
          <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
            요청한 프로젝트가 존재하지 않거나 삭제되었습니다.
          </p>
          <Link href="/projects" className="brand-button mt-6">
            <ArrowLeft className="h-4 w-4" />
            프로젝트 목록으로
          </Link>
        </div>
      </AppShell>
    );
  }

  const badge = STATUS_BADGE[project.status] ?? STATUS_BADGE.active;

  return (
    <AppShell
      header={
        <TopBar
          title={project.name}
          subtitle={project.description || undefined}
          href="/projects"
          action={
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowLinkDoc((prev) => !prev)}
                className="secondary-button"
              >
                <Link2 className="h-4 w-4" />
                문서 연결
              </button>
              <button
                onClick={() => setShowSettings((prev) => !prev)}
                className="secondary-button"
              >
                <Settings className="h-4 w-4" />
                설정
              </button>
            </div>
          }
        />
      }
    >
      <section className="section-card">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div>
            <p className="data-label">프로젝트 개요</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <h2 className="text-3xl font-semibold tracking-[-0.05em] text-slate-900">{project.name}</h2>
              <span className={`pill-badge ${badge.className}`}>{badge.label}</span>
            </div>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">{project.description || "프로젝트 설명이 없습니다."}</p>
            {(project.tags ?? []).length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {(project.tags ?? []).map((tag) => (
                  <span key={tag} className="pill-badge bg-slate-100 text-slate-600">
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}
          </div>

          <aside className="grid gap-3 sm:grid-cols-2 xl:grid-cols-2">
            <ProjectStatTile label="전체 문서" value={stats.total || 0} />
            <ProjectStatTile label="PRD" value={stats.PRD || 0} />
            <ProjectStatTile label="TRD" value={stats.TRD || 0} />
            <ProjectStatTile label="WBS" value={stats.WBS || 0} />
            <ProjectStatTile label="제안서" value={stats.Proposal || 0} />
            <ProjectStatTile label="PPT" value={stats.PPT || 0} />
          </aside>
        </div>
      </section>

      {/* Link Document Form */}
      {showLinkDoc ? (
        <LinkDocumentSection
          projectId={projectId}
          onClose={() => setShowLinkDoc(false)}
        />
      ) : null}

      {/* Documents grouped by type */}
      <section className="section-card">
        <SectionHeader
          title="프로젝트 문서"
          description="타입별로 분류된 프로젝트 문서 목록입니다."
        />

        {docs.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-[1.4rem] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-6 py-16 text-center">
            <FolderOpen className="h-12 w-12 text-slate-400" />
            <p className="mt-3 text-base font-semibold text-slate-800">연결된 문서가 없습니다</p>
            <p className="mt-1.5 max-w-md text-sm text-slate-500">
              위의 &quot;문서 연결&quot; 버튼으로 기존 문서를 이 프로젝트에 추가하세요.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedDocs).map(([type, typeDocs]) => {
              const meta = DOC_TYPE_META[type] ?? DOC_TYPE_META.PRD;
              const Icon = meta.icon;
              return (
                <div key={type}>
                  <div className="mb-3 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] text-slate-700">
                      <Icon className="h-4 w-4" />
                    </div>
                    <h4 className="text-base font-semibold text-slate-900">
                      {meta.label}
                    </h4>
                    <span className="rounded-md bg-[var(--bg-panel-muted)] px-2 py-0.5 text-xs font-medium text-[var(--text-muted)]">
                      {typeDocs.length}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {typeDocs.map((doc) => (
                      <DocumentRow
                        key={doc.doc_id}
                        doc={doc}
                        onRemove={() => removeDocMutation.mutate(doc.doc_id)}
                        isRemoving={removeDocMutation.isPending}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Project Settings */}
      {showSettings ? (
        <ProjectSettingsSection
          project={project}
          onClose={() => setShowSettings(false)}
          onDelete={handleDeleteProject}
          isDeleting={deleteMutation.isPending}
        />
      ) : null}
    </AppShell>
  );
}

/* -------------------------------------------------------------------------- */
/*  Document Row                                                               */
/* -------------------------------------------------------------------------- */

function DocumentRow({
  doc,
  onRemove,
  isRemoving,
}: {
  doc: DocumentReference;
  onRemove: () => void;
  isRemoving: boolean;
}) {
  const meta = DOC_TYPE_META[doc.doc_type] ?? DOC_TYPE_META.PRD;
  const viewerPath = getDocViewerPath(doc.doc_type, doc.doc_id);
  const isPPT = doc.doc_type === "PPT";

  const content = (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-center gap-3">
        <span className={`h-2 w-2 shrink-0 rounded-full ${meta.dotColor}`} />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-900">
            {doc.title || doc.doc_id}
          </p>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1">
              <Clock3 className="h-3 w-3" />
              {formatDate(doc.created_at ?? "", {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            <span className="inline-flex items-center gap-1 text-[#0F7B6C]">
              <CheckCircle2 className="h-3 w-3" />
              생성 완료
            </span>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {isPPT ? (
          <button
            onClick={async (e) => {
              e.preventDefault();
              e.stopPropagation();
              try {
                await api.openPptxFile(doc.doc_id);
              } catch (error) {
                console.error("PPTX 파일을 열지 못했습니다.", error);
                alert("PPTX 파일을 열지 못했습니다.");
              }
            }}
            className="brand-button !rounded-md !px-3 !py-1.5"
          >
            <Presentation className="h-3.5 w-3.5" />
            PPTX 열기
          </button>
        ) : null}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onRemove();
          }}
          disabled={isRemoving}
          className="secondary-button disabled:opacity-50"
          title="프로젝트에서 문서 연결 해제"
        >
          {isRemoving ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <X className="h-3.5 w-3.5 text-[#E03E3E]" />
          )}
        </button>
      </div>
    </div>
  );

  if (viewerPath) {
    return (
      <Link href={viewerPath} className="list-card group block">
        {content}
      </Link>
    );
  }

  return <div className="list-card">{content}</div>;
}

function ProjectStatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="surface-muted p-4">
      <p className="data-label">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-slate-900">{value}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Link Document Section                                                      */
/* -------------------------------------------------------------------------- */

function LinkDocumentSection({
  projectId,
  onClose,
}: {
  projectId: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [selectedDocId, setSelectedDocId] = useState("");

  /* -- Fetch available documents -- */
  const { data: outputsData, isLoading: docsLoading } = useQuery({
    queryKey: ["output-documents"],
    queryFn: () => api.listOutputDocuments(),
  });

  const availableDocs = useMemo(
    () => outputsData?.documents ?? [],
    [outputsData?.documents]
  );

  /* -- Add document mutation -- */
  const addMutation = useMutation({
    mutationFn: () => {
      const doc = availableDocs.find((d) => d.id === selectedDocId);
      if (!doc) throw new Error("문서를 찾을 수 없습니다");
      return api.addDocumentToProject(projectId, doc.id, doc.doc_type, doc.title);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project-documents", projectId] });
      setSelectedDocId("");
    },
  });

  function handleAdd() {
    if (!selectedDocId) return;
    addMutation.mutate();
  }

  return (
    <section className="section-card">
      <SectionHeader
        title="문서 연결"
        description="기존 생성 문서를 이 프로젝트에 연결합니다."
        action={
          <button onClick={onClose} className="secondary-button !rounded-md !px-3 !py-1.5">
            <X className="h-4 w-4" />
            닫기
          </button>
        }
      />

      {docsLoading ? (
        <div className="flex items-center gap-2 py-4">
          <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
          <span className="text-sm text-slate-500">문서 목록을 불러오는 중...</span>
        </div>
      ) : availableDocs.length === 0 ? (
        <p className="py-4 text-sm text-slate-500">연결할 수 있는 문서가 없습니다.</p>
      ) : (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="data-label mb-1.5 block">문서 선택</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
            >
              <option value="">문서를 선택하세요</option>
              {availableDocs.map((doc) => {
                const meta = DOC_TYPE_META[doc.doc_type];
                return (
                  <option key={doc.id} value={doc.id}>
                    [{meta?.shortLabel || doc.doc_type}] {doc.title}
                  </option>
                );
              })}
            </select>
          </div>
          <button
            onClick={handleAdd}
            disabled={!selectedDocId || addMutation.isPending}
            className="brand-button disabled:cursor-not-allowed disabled:opacity-50"
          >
            {addMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Link2 className="h-4 w-4" />
            )}
            연결
          </button>
        </div>
      )}
      {addMutation.isError ? (
        <p className="mt-2 text-sm text-[#E03E3E]">문서 연결에 실패했습니다.</p>
      ) : null}
      {addMutation.isSuccess ? (
        <p className="mt-2 text-sm text-[#0F7B6C]">문서가 연결되었습니다.</p>
      ) : null}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Project Settings Section                                                   */
/* -------------------------------------------------------------------------- */

function ProjectSettingsSection({
  project,
  onClose,
  onDelete,
  isDeleting,
}: {
  project: { id: string; name: string; description: string; status: string; tags: string[] };
  onClose: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  const queryClient = useQueryClient();
  const [editName, setEditName] = useState(project.name);
  const [editDescription, setEditDescription] = useState(project.description);
  const [editStatus, setEditStatus] = useState(project.status);
  const [editTags, setEditTags] = useState((project.tags ?? []).join(", "));

  const updateMutation = useMutation({
    mutationFn: () => {
      const tags = editTags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      return api.updateProject(project.id, {
        name: editName.trim(),
        description: editDescription.trim(),
        status: editStatus,
        tags,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", project.id] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!editName.trim()) return;
    updateMutation.mutate();
  }

  return (
    <section className="section-card">
      <SectionHeader
        title="프로젝트 설정"
        description="프로젝트 정보를 수정하거나 삭제합니다."
        action={
          <button onClick={onClose} className="secondary-button !rounded-md !px-3 !py-1.5">
            <X className="h-4 w-4" />
            닫기
          </button>
        }
      />

      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="data-label mb-1.5 block">프로젝트 이름</label>
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            required
            className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 placeholder:text-[var(--text-muted)] focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
          />
        </div>
        <div>
          <label className="data-label mb-1.5 block">설명</label>
          <textarea
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            rows={3}
            className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 placeholder:text-[var(--text-muted)] focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
          />
        </div>
        <div>
          <label className="data-label mb-1.5 block">상태</label>
          <select
            value={editStatus}
            onChange={(e) => setEditStatus(e.target.value)}
            className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="data-label mb-1.5 block">태그</label>
          <input
            type="text"
            value={editTags}
            onChange={(e) => setEditTags(e.target.value)}
            placeholder="쉼표로 구분 (예: 웹앱, 모바일, MVP)"
            className="w-full rounded-xl border border-[var(--line-strong)] bg-[var(--bg-deep)] px-4 py-3 text-sm text-slate-900 placeholder:text-[var(--text-muted)] focus:border-[#2383E2] focus:outline-none focus:ring-2 focus:ring-[#2383E2]/20"
          />
        </div>
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={!editName.trim() || updateMutation.isPending}
            className="brand-button disabled:cursor-not-allowed disabled:opacity-50"
          >
            {updateMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Settings className="h-4 w-4" />
            )}
            저장
          </button>
          {updateMutation.isSuccess ? (
            <span className="text-sm text-[#0F7B6C]">저장되었습니다.</span>
          ) : null}
          {updateMutation.isError ? (
            <span className="text-sm text-[#E03E3E]">저장에 실패했습니다.</span>
          ) : null}
        </div>
      </form>

      {/* Danger zone */}
      <div className="mt-8 rounded-xl border border-[#E03E3E]/20 bg-[#E03E3E]/5 p-5">
        <h4 className="text-sm font-semibold text-[#E03E3E]">위험 영역</h4>
        <p className="mt-1.5 text-sm text-slate-500">
          프로젝트를 삭제하면 프로젝트와 문서 연결 정보가 영구적으로 제거됩니다.
          연결된 문서 파일 자체는 삭제되지 않습니다.
        </p>
        <button
          onClick={onDelete}
          disabled={isDeleting}
          className="mt-4 inline-flex items-center gap-2 rounded-xl border border-[#E03E3E]/30 bg-white px-4 py-2.5 text-sm font-semibold text-[#E03E3E] transition-colors hover:bg-[#E03E3E]/5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isDeleting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
          프로젝트 삭제
        </button>
      </div>
    </section>
  );
}
