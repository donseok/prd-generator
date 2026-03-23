"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  Code2,
  Download,
  ListChecks,
  Loader2,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { AppShell, SectionHeader, TopBar, formatDate } from "@/components/app-shell";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface WBSTask {
  id: string;
  name: string;
  estimated_hours: number;
  dependencies: string[];
  assigned_role: string;
  status: string;
}

interface WorkPackage {
  id: string;
  name: string;
  description: string;
  tasks: WBSTask[];
}

interface WBSPhase {
  id: string;
  name: string;
  description: string;
  order: number;
  work_packages: WorkPackage[];
}

interface WBSSummary {
  total_hours?: number;
  man_months?: number;
  total_tasks?: number;
  critical_path?: string[];
}

interface WBSContext {
  start_date?: string;
  team_size?: number;
  methodology?: string;
  sprint_duration?: number;
  [key: string]: unknown;
}

interface WBSMetadata {
  version?: string;
  created_at?: string;
  source_prd_id?: string;
}

interface WBSData {
  title?: string;
  context?: WBSContext;
  phases?: WBSPhase[];
  summary?: WBSSummary;
  metadata?: WBSMetadata;
}

/* ------------------------------------------------------------------ */
/*  Tabs                                                               */
/* ------------------------------------------------------------------ */

type TabKey = "summary" | "phases" | "tasks";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "summary", label: "요약" },
  { key: "phases", label: "페이즈" },
  { key: "tasks", label: "태스크 목록" },
];

const WBS_ACCENT = "#0F7B6C";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-slate-100 text-slate-600",
  "in-progress": "bg-blue-100 text-blue-700",
  in_progress: "bg-blue-100 text-blue-700",
  completed: "bg-emerald-100 text-emerald-700",
  blocked: "bg-rose-100 text-rose-700",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "대기",
  "in-progress": "진행 중",
  in_progress: "진행 중",
  completed: "완료",
  blocked: "차단됨",
};

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function WBSViewerPage() {
  const params = useParams();
  const docId = params.id as string;
  const [activeTab, setActiveTab] = useState<TabKey>("summary");
  const [rawView, setRawView] = useState<"json" | "md" | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["wbs-doc", docId],
    queryFn: () => api.getOutputDocument(docId, "json"),
    enabled: !!docId,
  });

  const { data: mdData } = useQuery({
    queryKey: ["wbs-doc-md", docId],
    queryFn: () => api.getOutputDocument(docId, "md"),
    enabled: rawView === "md",
  });

  const wbs = (data?.content_json ?? {}) as WBSData;

  const allTasks = useMemo(() => {
    const tasks: Array<WBSTask & { phaseName: string; packageName: string }> = [];
    for (const phase of wbs.phases ?? []) {
      for (const pkg of phase.work_packages ?? []) {
        for (const task of pkg.tasks ?? []) {
          tasks.push({ ...task, phaseName: phase.name, packageName: pkg.name });
        }
      }
    }
    return tasks;
  }, [wbs.phases]);

  async function handleDownload(format: "json" | "md") {
    const result = await api.getOutputDocument(docId, format);
    const content = format === "json"
      ? JSON.stringify(result.content_json, null, 2)
      : (result.content_md ?? "");
    const blob = new Blob([content], { type: format === "json" ? "application/json" : "text/plain" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `wbs-${docId}.${format === "json" ? "json" : "md"}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading) {
    return (
      <AppShell header={<TopBar title="WBS 상세" subtitle="문서를 불러오는 중입니다" href="/history" />}>
        <section className="section-card flex items-center justify-center py-20">
          <Loader2 className="h-10 w-10 animate-spin" style={{ color: WBS_ACCENT }} />
        </section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell header={<TopBar title="WBS 상세" subtitle="문서를 찾을 수 없습니다" href="/history" />}>
        <section className="section-card">
          <div className="flex flex-col items-center justify-center px-6 py-20 text-center">
            <AlertCircle className="h-10 w-10 text-[#E03E3E]" />
            <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">WBS를 불러오지 못했습니다</p>
            <Link href="/history" className="mt-6 brand-button">돌아가기</Link>
          </div>
        </section>
      </AppShell>
    );
  }

  const summary = wbs.summary ?? {};

  return (
    <AppShell
      header={
        <TopBar
          title={wbs.title ?? "WBS 문서"}
          subtitle={`${wbs.metadata?.version ? `버전 ${wbs.metadata.version} ` : ""}${wbs.metadata?.created_at ? `${formatDate(wbs.metadata.created_at)}` : ""}`}
          href="/history"
          action={
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setRawView(rawView === "json" ? null : "json")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Code2 className="h-4 w-4" /> JSON 보기
              </button>
              <button onClick={() => setRawView(rawView === "md" ? null : "md")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Code2 className="h-4 w-4" /> Markdown 보기
              </button>
              <button onClick={() => handleDownload("json")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Download className="h-4 w-4" /> JSON
              </button>
              <button onClick={() => handleDownload("md")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Download className="h-4 w-4" /> MD
              </button>
            </div>
          }
        />
      }
    >
      {/* Raw view overlay */}
      {rawView ? (
        <section className="section-card">
          <SectionHeader
            title={rawView === "json" ? "JSON 원본" : "Markdown 원본"}
            action={
              <button onClick={() => setRawView(null)} className="secondary-button !rounded-xl !px-3 !py-1.5">닫기</button>
            }
          />
          <pre className="mt-4 max-h-[600px] overflow-auto rounded-xl bg-slate-50 p-5 text-xs leading-6 text-slate-700">
            {rawView === "json"
              ? JSON.stringify(wbs, null, 2)
              : (mdData?.content_md ?? "Markdown 데이터를 불러오는 중입니다...")}
          </pre>
        </section>
      ) : null}

      <section className="section-card">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div>
            <p className="data-label">실행 계획 개요</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-slate-900">{wbs.title ?? "WBS 문서"}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
              페이즈, 작업 패키지, 태스크를 하나의 실행 계획 문서처럼 읽을 수 있게 정리했습니다. 요약 수치만 먼저 보고 바로 페이즈와 태스크 본문으로 이어집니다.
            </p>
          </div>

          <aside className="grid gap-3 sm:grid-cols-2 xl:grid-cols-2">
            <MetaTile label="총 공수" value={summary.total_hours != null ? `${summary.total_hours.toLocaleString()}h` : "-"} />
            <MetaTile label="총 태스크" value={String(summary.total_tasks ?? allTasks.length)} />
            <MetaTile label="페이즈" value={String(wbs.phases?.length ?? 0)} />
            <MetaTile label="팀 규모" value={wbs.context?.team_size != null ? `${wbs.context.team_size}명` : "-"} />
          </aside>
        </div>
      </section>

      {/* Tabs */}
      <section className="section-card">
        <div className="mb-6 flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`tab-button ${activeTab === tab.key ? "tab-button-active" : "tab-button-idle"}`}
            >
              {tab.label}
              {tab.key === "phases" ? ` (${wbs.phases?.length ?? 0})` : ""}
              {tab.key === "tasks" ? ` (${allTasks.length})` : ""}
            </button>
          ))}
        </div>

        {activeTab === "summary" ? <SummaryTab wbs={wbs} allTasks={allTasks} /> : null}
        {activeTab === "phases" ? <PhasesTab phases={wbs.phases ?? []} /> : null}
        {activeTab === "tasks" ? <TasksTab tasks={allTasks} /> : null}
      </section>
    </AppShell>
  );
}

function MetaTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="surface-muted p-4">
      <p className="data-label">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-slate-900">{value}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Summary Tab                                                        */
/* ------------------------------------------------------------------ */

function SummaryTab({ wbs, allTasks }: { wbs: WBSData; allTasks: Array<WBSTask & { phaseName: string }> }) {
  const summary = wbs.summary ?? {};
  const ctx = wbs.context ?? {};

  // Role distribution
  const roleMap = useMemo(() => {
    const map: Record<string, number> = {};
    for (const task of allTasks) {
      const role = task.assigned_role || "미지정";
      map[role] = (map[role] ?? 0) + task.estimated_hours;
    }
    return Object.entries(map).sort(([, a], [, b]) => b - a);
  }, [allTasks]);

  return (
    <div className="space-y-6">
      {/* Context Info */}
      <div>
        <SectionHeader title="프로젝트 컨텍스트" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ContextCard label="시작일" value={ctx.start_date != null && typeof ctx.start_date !== "object" ? String(ctx.start_date) : "-"} icon={<Clock className="h-4 w-4" style={{ color: WBS_ACCENT }} />} />
          <ContextCard label="팀 규모" value={ctx.team_size != null ? `${ctx.team_size}명` : "-"} icon={<Users className="h-4 w-4" style={{ color: WBS_ACCENT }} />} />
          <ContextCard label="방법론" value={ctx.methodology != null && typeof ctx.methodology !== "object" ? String(ctx.methodology) : "-"} icon={<ListChecks className="h-4 w-4" style={{ color: WBS_ACCENT }} />} />
          <ContextCard label="스프린트 주기" value={ctx.sprint_duration != null ? `${ctx.sprint_duration}일` : "-"} icon={<Clock className="h-4 w-4" style={{ color: WBS_ACCENT }} />} />
        </div>
      </div>

      {/* Summary Metrics */}
      <div>
        <SectionHeader title="공수 요약" />
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="list-card" style={{ borderLeft: `3px solid ${WBS_ACCENT}` }}>
            <p className="data-label">총 시간</p>
            <p className="mt-2 text-2xl font-extrabold tracking-tight text-slate-900">
              {summary.total_hours != null ? `${summary.total_hours.toLocaleString()}h` : "-"}
            </p>
          </div>
          <div className="list-card" style={{ borderLeft: `3px solid ${WBS_ACCENT}` }}>
            <p className="data-label">M/M (인월)</p>
            <p className="mt-2 text-2xl font-extrabold tracking-tight text-slate-900">
              {summary.man_months ?? "-"}
            </p>
          </div>
          <div className="list-card" style={{ borderLeft: `3px solid ${WBS_ACCENT}` }}>
            <p className="data-label">총 태스크</p>
            <p className="mt-2 text-2xl font-extrabold tracking-tight text-slate-900">
              {summary.total_tasks ?? allTasks.length}
            </p>
          </div>
        </div>
      </div>

      {/* Role Distribution */}
      {roleMap.length > 0 ? (
        <div>
          <SectionHeader title="역할별 공수 분포" description="각 역할에 배정된 총 시간" />
          <div className="space-y-3">
            {roleMap.map(([role, hours]) => {
              const total = summary.total_hours || 1;
              const percent = Math.round((hours / total) * 100);
              return (
                <div key={role} className="list-card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{role}</p>
                      <p className="mt-1 text-xs text-slate-500">{hours}h ({percent}%)</p>
                    </div>
                    <div className="w-32">
                      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                        <div className="h-full rounded-full" style={{ width: `${percent}%`, background: WBS_ACCENT }} />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* Critical Path */}
      {Array.isArray(summary.critical_path) && summary.critical_path.length > 0 ? (
        <div>
          <SectionHeader title="크리티컬 패스" description="프로젝트 일정에 직접 영향을 미치는 핵심 경로" />
          <div className="surface-muted p-5">
            <div className="flex flex-wrap gap-2">
              {summary.critical_path.map((item, index) => (
                <span key={index} className="flex items-center gap-2">
                  <span className="pill-badge bg-[#0F7B6C]/10 text-[#0F7B6C] font-semibold">{item}</span>
                  {index < (summary.critical_path?.length ?? 0) - 1 ? (
                    <span className="text-slate-400">-&gt;</span>
                  ) : null}
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ContextCard({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="list-card">
      <div className="mb-2 flex items-center gap-2">
        {icon}
        <p className="data-label">{label}</p>
      </div>
      <p className="text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Phases Tab                                                         */
/* ------------------------------------------------------------------ */

function PhasesTab({ phases }: { phases: WBSPhase[] }) {
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());
  const [expandedPackages, setExpandedPackages] = useState<Set<string>>(new Set());

  function togglePhase(id: string) {
    setExpandedPhases((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function togglePackage(id: string) {
    setExpandedPackages((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const safePhases = Array.isArray(phases) ? phases : [];

  if (!safePhases.length) {
    return <EmptyPanel title="페이즈 정보가 없습니다" />;
  }

  return (
    <div className="space-y-4">
      {safePhases
        .slice()
        .sort((a, b) => a.order - b.order)
        .map((phase) => {
          const phaseExpanded = expandedPhases.has(phase.id);
          const safeWorkPackages = Array.isArray(phase.work_packages) ? phase.work_packages : [];
          const phaseHours = safeWorkPackages.reduce(
            (sum, pkg) => sum + (Array.isArray(pkg.tasks) ? pkg.tasks : []).reduce((s, t) => s + (t.estimated_hours || 0), 0),
            0
          );
          const phaseTasks = safeWorkPackages.reduce((sum, pkg) => sum + (Array.isArray(pkg.tasks) ? pkg.tasks : []).length, 0);

          return (
            <div key={phase.id} className="rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel)]">
              {/* Phase header */}
              <button onClick={() => togglePhase(phase.id)} className="flex w-full items-start gap-4 p-5 text-left">
                <div className="mt-1 text-slate-400">
                  {phaseExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </div>
                <div
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white"
                  style={{ background: WBS_ACCENT }}
                >
                  P{phase.order}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-base font-bold tracking-[-0.03em] text-slate-900">{phase.name}</p>
                  <p className="mt-1 text-sm text-slate-600">{phase.description}</p>
                  <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                    <span>{safeWorkPackages.length}개 작업 패키지</span>
                    <span>{phaseTasks}개 태스크</span>
                    <span>{phaseHours}h</span>
                  </div>
                </div>
              </button>

              {/* Work packages */}
              {phaseExpanded ? (
                <div className="border-t border-[var(--line-soft)] px-5 pb-5 pl-14 pt-5">
                  <div className="space-y-3">
                    {safeWorkPackages.map((pkg) => {
                      const pkgExpanded = expandedPackages.has(pkg.id);
                      const safePkgTasks = Array.isArray(pkg.tasks) ? pkg.tasks : [];
                      const pkgHours = safePkgTasks.reduce((sum, t) => sum + (t.estimated_hours || 0), 0);
                      return (
                        <div key={pkg.id} className="rounded-xl border border-[var(--line-soft)] bg-[var(--bg-panel)]">
                          <button onClick={() => togglePackage(pkg.id)} className="flex w-full items-start gap-3 p-4 text-left">
                            <div className="mt-0.5 text-slate-400">
                              {pkgExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="pill-badge bg-[#0F7B6C]/10 text-[#0F7B6C]">{pkg.id}</span>
                                <span className="text-sm font-semibold text-slate-900">{pkg.name}</span>
                              </div>
                              <p className="mt-1 text-xs text-slate-500">{safePkgTasks.length}개 태스크 / {pkgHours}h</p>
                            </div>
                          </button>

                          {pkgExpanded ? (
                            <div className="border-t border-[var(--line-soft)] p-4 pl-10">
                              {pkg.description ? (
                                <p className="mb-3 text-sm text-slate-600">{pkg.description}</p>
                              ) : null}
                              <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                  <thead>
                                    <tr className="border-b border-slate-200 text-left">
                                      <th className="px-2 py-2 font-semibold text-slate-900">ID</th>
                                      <th className="px-2 py-2 font-semibold text-slate-900">태스크명</th>
                                      <th className="px-2 py-2 font-semibold text-slate-900">시간</th>
                                      <th className="px-2 py-2 font-semibold text-slate-900">역할</th>
                                      <th className="px-2 py-2 font-semibold text-slate-900">상태</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {safePkgTasks.map((task) => (
                                      <tr key={task.id} className="border-b border-slate-100">
                                        <td className="px-2 py-2 font-mono text-xs text-slate-500">{task.id}</td>
                                        <td className="px-2 py-2 font-medium text-slate-900">{task.name}</td>
                                        <td className="px-2 py-2 text-slate-700">{task.estimated_hours}h</td>
                                        <td className="px-2 py-2">
                                          <span className="pill-badge bg-slate-100 text-slate-600">{task.assigned_role || "-"}</span>
                                        </td>
                                        <td className="px-2 py-2">
                                          <span className={`pill-badge ${STATUS_STYLE[task.status] ?? STATUS_STYLE.pending}`}>
                                            {STATUS_LABEL[task.status] ?? task.status}
                                          </span>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Tasks Tab (Flat table)                                             */
/* ------------------------------------------------------------------ */

function TasksTab({ tasks }: { tasks: Array<WBSTask & { phaseName: string; packageName: string }> }) {
  const [sortField, setSortField] = useState<"id" | "hours" | "role" | "status">("id");
  const [sortAsc, setSortAsc] = useState(true);

  function handleSort(field: typeof sortField) {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  }

  const sortedTasks = useMemo(() => {
    const sorted = [...(Array.isArray(tasks) ? tasks : [])];
    sorted.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "id":
          cmp = a.id.localeCompare(b.id);
          break;
        case "hours":
          cmp = a.estimated_hours - b.estimated_hours;
          break;
        case "role":
          cmp = (a.assigned_role || "").localeCompare(b.assigned_role || "");
          break;
        case "status":
          cmp = (a.status || "").localeCompare(b.status || "");
          break;
      }
      return sortAsc ? cmp : -cmp;
    });
    return sorted;
  }, [tasks, sortField, sortAsc]);

  if (!Array.isArray(tasks) || !tasks.length) {
    return <EmptyPanel title="태스크 정보가 없습니다" />;
  }

  const sortIndicator = (field: typeof sortField) => {
    if (sortField !== field) return "";
    return sortAsc ? " ^" : " v";
  };

  return (
    <div>
      <SectionHeader title="전체 태스크 목록" description={`총 ${tasks.length}개 태스크`} />
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left">
              <th className="cursor-pointer px-3 py-3 font-semibold text-slate-900" onClick={() => handleSort("id")}>
                ID{sortIndicator("id")}
              </th>
              <th className="px-3 py-3 font-semibold text-slate-900">태스크명</th>
              <th className="cursor-pointer px-3 py-3 font-semibold text-slate-900" onClick={() => handleSort("hours")}>
                시간{sortIndicator("hours")}
              </th>
              <th className="cursor-pointer px-3 py-3 font-semibold text-slate-900" onClick={() => handleSort("role")}>
                역할{sortIndicator("role")}
              </th>
              <th className="px-3 py-3 font-semibold text-slate-900">의존성</th>
              <th className="cursor-pointer px-3 py-3 font-semibold text-slate-900" onClick={() => handleSort("status")}>
                상태{sortIndicator("status")}
              </th>
              <th className="px-3 py-3 font-semibold text-slate-900">페이즈</th>
            </tr>
          </thead>
          <tbody>
            {sortedTasks.map((task) => (
              <tr key={task.id} className="border-b border-slate-100">
                <td className="px-3 py-3 font-mono text-xs text-slate-500">{task.id}</td>
                <td className="px-3 py-3 font-medium text-slate-900">{task.name}</td>
                <td className="px-3 py-3 text-slate-700">{task.estimated_hours}h</td>
                <td className="px-3 py-3">
                  <span className="pill-badge bg-slate-100 text-slate-600">{task.assigned_role || "-"}</span>
                </td>
                <td className="px-3 py-3">
                  {Array.isArray(task.dependencies) && task.dependencies.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {task.dependencies.map((dep, i) => {
                        const label = typeof dep === "string" ? dep : (dep as Record<string, unknown>).predecessor_id ?? JSON.stringify(dep);
                        return <span key={i} className="pill-badge bg-[#0F7B6C]/10 text-[#0F7B6C] text-xs">{String(label)}</span>;
                      })}
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400">-</span>
                  )}
                </td>
                <td className="px-3 py-3">
                  <span className={`pill-badge ${STATUS_STYLE[task.status] ?? STATUS_STYLE.pending}`}>
                    {STATUS_LABEL[task.status] ?? task.status}
                  </span>
                </td>
                <td className="px-3 py-3 text-xs text-slate-500">{task.phaseName}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Utilities                                                          */
/* ------------------------------------------------------------------ */

function EmptyPanel({ title }: { title: string }) {
  return (
    <div className="surface-muted flex items-center justify-center rounded-2xl px-6 py-16 text-center">
      <p className="text-base font-semibold text-slate-700">{title}</p>
    </div>
  );
}
