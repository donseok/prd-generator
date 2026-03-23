"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  Briefcase,
  Calendar,
  CheckCircle2,
  Code2,
  Download,
  Loader2,
  ShieldAlert,
  Target,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { AppShell, SectionHeader, TopBar, formatDate } from "@/components/app-shell";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ProjectOverview {
  background?: string;
  objectives?: string[];
  scope?: string;
}

interface ScopeOfWork {
  in_scope?: string[];
  out_of_scope?: string[];
  deliverables?: string[];
}

interface SolutionApproach {
  methodology?: string;
  key_features?: string[];
  innovation_points?: string[];
}

interface TimelinePhase {
  name: string;
  duration: string;
  deliverables: string[];
}

interface Timeline {
  total_duration?: string;
  phases?: TimelinePhase[];
}

interface TeamMember {
  role: string;
  count: number;
  responsibilities: string[];
}

interface ResourcePlan {
  team_members?: TeamMember[];
  total_man_months?: number;
}

interface Risk {
  description: string;
  level: string;
  impact: string;
  mitigation: string;
}

interface RiskManagement {
  risks?: Risk[];
}

interface ProposalMetadata {
  version?: string;
  created_at?: string;
  source_prd_id?: string;
}

interface ProposalData {
  title?: string;
  project_overview?: ProjectOverview;
  executive_summary?: string;
  scope_of_work?: ScopeOfWork;
  solution_approach?: SolutionApproach;
  timeline?: Timeline;
  resource_plan?: ResourcePlan;
  risk_management?: RiskManagement;
  metadata?: ProposalMetadata;
}

/* ------------------------------------------------------------------ */
/*  Tabs                                                               */
/* ------------------------------------------------------------------ */

type TabKey = "executive" | "scope" | "timeline" | "risk";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "executive", label: "경영진 요약" },
  { key: "scope", label: "범위 및 솔루션" },
  { key: "timeline", label: "일정 및 리소스" },
  { key: "risk", label: "리스크 관리" },
];

const PROPOSAL_ACCENT = "#D9730D";

const RISK_LEVEL_STYLE: Record<string, string> = {
  HIGH: "bg-rose-100 text-rose-700",
  MEDIUM: "bg-amber-100 text-amber-700",
  LOW: "bg-emerald-100 text-emerald-700",
};

const RISK_LEVEL_LABEL: Record<string, string> = {
  HIGH: "높음",
  MEDIUM: "보통",
  LOW: "낮음",
};

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function ProposalViewerPage() {
  const params = useParams();
  const docId = params.id as string;
  const [activeTab, setActiveTab] = useState<TabKey>("executive");
  const [rawView, setRawView] = useState<"json" | "md" | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["proposal-doc", docId],
    queryFn: () => api.getOutputDocument(docId, "json"),
    enabled: !!docId,
  });

  const { data: mdData } = useQuery({
    queryKey: ["proposal-doc-md", docId],
    queryFn: () => api.getOutputDocument(docId, "md"),
    enabled: rawView === "md",
  });

  const proposal = (data?.content_json ?? {}) as ProposalData;

  async function handleDownload(format: "json" | "md") {
    const result = await api.getOutputDocument(docId, format);
    const content = format === "json"
      ? JSON.stringify(result.content_json, null, 2)
      : (result.content_md ?? "");
    const blob = new Blob([content], { type: format === "json" ? "application/json" : "text/plain" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `proposal-${docId}.${format === "json" ? "json" : "md"}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading) {
    return (
      <AppShell header={<TopBar title="제안서 상세" subtitle="문서를 불러오는 중입니다" href="/history" />}>
        <section className="section-card flex items-center justify-center py-20">
          <Loader2 className="h-10 w-10 animate-spin" style={{ color: PROPOSAL_ACCENT }} />
        </section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell header={<TopBar title="제안서 상세" subtitle="문서를 찾을 수 없습니다" href="/history" />}>
        <section className="section-card">
          <div className="flex flex-col items-center justify-center px-6 py-20 text-center">
            <AlertCircle className="h-10 w-10 text-[#E03E3E]" />
            <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">제안서를 불러오지 못했습니다</p>
            <Link href="/history" className="mt-6 brand-button">돌아가기</Link>
          </div>
        </section>
      </AppShell>
    );
  }

  const risks = Array.isArray(proposal.risk_management?.risks) ? proposal.risk_management!.risks! : [];
  const highRisks = risks.filter((r) => r.level?.toUpperCase() === "HIGH").length;
  const rawTeamMembers = proposal.resource_plan?.team_members;
  const teamCount = Array.isArray(rawTeamMembers) ? rawTeamMembers.reduce((sum, m) => sum + (m.count || 0), 0) : 0;

  return (
    <AppShell
      header={
        <TopBar
          title={proposal.title ?? "제안서 문서"}
          subtitle={`${proposal.metadata?.version ? `버전 ${proposal.metadata.version} ` : ""}${proposal.metadata?.created_at ? `${formatDate(proposal.metadata.created_at)}` : ""}`}
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
              ? JSON.stringify(proposal, null, 2)
              : (mdData?.content_md ?? "Markdown 데이터를 불러오는 중입니다...")}
          </pre>
        </section>
      ) : null}

      <section className="section-card">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div>
            <p className="data-label">제안 문서 개요</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-slate-900">{proposal.title ?? "제안서 문서"}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
              제안서는 서사와 일정, 리스크를 같이 읽는 문서입니다. 상단 요약으로 규모와 기간을 먼저 보고, 아래 탭에서 제안 논리를 순서대로 읽을 수 있도록 정리했습니다.
            </p>
          </div>

          <aside className="grid gap-3 sm:grid-cols-2 xl:grid-cols-2">
            <MetaTile label="총 기간" value={proposal.timeline?.total_duration ?? "-"} />
            <MetaTile label="팀 규모" value={teamCount > 0 ? `${teamCount}명` : "-"} />
            <MetaTile label="리스크" value={String(risks.length)} />
            <MetaTile label="산출물" value={String(Array.isArray(proposal.scope_of_work?.deliverables) ? proposal.scope_of_work!.deliverables!.length : 0)} />
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
              {tab.key === "risk" ? ` (${risks.length})` : ""}
            </button>
          ))}
        </div>

        {activeTab === "executive" ? <ExecutiveTab proposal={proposal} /> : null}
        {activeTab === "scope" ? <ScopeTab proposal={proposal} /> : null}
        {activeTab === "timeline" ? <TimelineTab proposal={proposal} /> : null}
        {activeTab === "risk" ? <RiskTab risks={risks} /> : null}
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
/*  Executive Summary Tab                                              */
/* ------------------------------------------------------------------ */

function ExecutiveTab({ proposal }: { proposal: ProposalData }) {
  const overview = proposal.project_overview ?? {};

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="space-y-6">
        {/* Executive Summary */}
        {proposal.executive_summary ? (
          <div className="glass-panel-strong rounded-2xl p-6">
            <SectionHeader title="경영진 요약" />
            <div className="text-sm leading-8 text-slate-700 whitespace-pre-line">{proposal.executive_summary}</div>
          </div>
        ) : null}

        {/* Background */}
        {overview.background ? (
          <div className="glass-panel-strong rounded-2xl p-6">
            <SectionHeader title="프로젝트 배경" />
            <div className="text-sm leading-8 text-slate-700 whitespace-pre-line">{overview.background}</div>
          </div>
        ) : null}

        {/* Scope */}
        {overview.scope ? (
          <div className="surface-muted p-5">
            <SectionHeader title="프로젝트 범위" />
            <div className="text-sm leading-7 text-slate-700 whitespace-pre-line">{overview.scope}</div>
          </div>
        ) : null}
      </div>

      <aside className="space-y-4">
        {/* Objectives */}
        <div className="surface-muted p-5">
          <div className="mb-3 flex items-center gap-2">
            <Target className="h-4 w-4" style={{ color: PROPOSAL_ACCENT }} />
            <p className="text-base font-semibold text-slate-900">프로젝트 목표</p>
          </div>
          {Array.isArray(overview.objectives) && overview.objectives.length > 0 ? (
            <ul className="space-y-2 text-sm leading-6 text-slate-700">
              {overview.objectives.map((obj, index) => (
                <li key={index}>- {typeof obj === "object" ? JSON.stringify(obj) : obj}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">정의된 목표가 없습니다</p>
          )}
        </div>

        {/* Metadata */}
        <div className="surface-muted p-5">
          <p className="data-label">문서 정보</p>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            {proposal.metadata?.version ? <p>버전: {proposal.metadata.version}</p> : null}
            {proposal.metadata?.created_at ? <p>생성일: {formatDate(proposal.metadata.created_at)}</p> : null}
            {proposal.metadata?.source_prd_id ? <p>원본 PRD: {proposal.metadata.source_prd_id}</p> : null}
          </div>
        </div>
      </aside>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Scope & Solution Tab                                               */
/* ------------------------------------------------------------------ */

function ScopeTab({ proposal }: { proposal: ProposalData }) {
  const scope = proposal.scope_of_work ?? {};
  const solution = proposal.solution_approach ?? {};

  return (
    <div className="space-y-8">
      {/* Scope of Work */}
      <div className="grid gap-6 lg:grid-cols-3">
        <ScopeCard
          title="범위 내"
          items={scope.in_scope}
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-600" />}
          emptyLabel="정의된 범위가 없습니다"
          accentColor="#0F7B6C"
        />
        <ScopeCard
          title="범위 외"
          items={scope.out_of_scope}
          icon={<AlertCircle className="h-4 w-4 text-slate-500" />}
          emptyLabel="정의된 범위 외 항목이 없습니다"
          accentColor="#9B9A97"
        />
        <ScopeCard
          title="산출물"
          items={scope.deliverables}
          icon={<Briefcase className="h-4 w-4" style={{ color: PROPOSAL_ACCENT }} />}
          emptyLabel="정의된 산출물이 없습니다"
          accentColor={PROPOSAL_ACCENT}
        />
      </div>

      {/* Solution Approach */}
      <div>
        <SectionHeader title="솔루션 접근 방식" />
        <div className="space-y-4">
          {solution.methodology ? (
            <div className="list-card" style={{ borderLeft: `3px solid ${PROPOSAL_ACCENT}` }}>
              <p className="data-label">방법론</p>
              <p className="mt-2 text-sm font-semibold text-slate-900">{solution.methodology}</p>
            </div>
          ) : null}

          {Array.isArray(solution.key_features) && solution.key_features.length > 0 ? (
            <div>
              <p className="mb-3 text-sm font-semibold text-slate-900">핵심 기능</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {solution.key_features.map((feature, index) => (
                  <div key={index} className="list-card">
                    <div className="flex items-start gap-3">
                      <div
                        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white"
                        style={{ background: PROPOSAL_ACCENT }}
                      >
                        {index + 1}
                      </div>
                      <p className="text-sm leading-6 text-slate-700">{typeof feature === "object" ? JSON.stringify(feature) : feature}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {Array.isArray(solution.innovation_points) && solution.innovation_points.length > 0 ? (
            <div>
              <p className="mb-3 text-sm font-semibold text-slate-900">혁신 포인트</p>
              <div className="surface-muted p-5">
                <ul className="space-y-2 text-sm leading-7 text-slate-700">
                  {solution.innovation_points.map((point, index) => (
                    <li key={index}>- {typeof point === "object" ? JSON.stringify(point) : point}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ScopeCard({
  title,
  items,
  icon,
  emptyLabel,
  accentColor,
}: {
  title: string;
  items?: string[];
  icon: React.ReactNode;
  emptyLabel: string;
  accentColor: string;
}) {
  return (
    <div className="list-card" style={{ borderLeft: `3px solid ${accentColor}` }}>
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <p className="text-base font-semibold text-slate-900">{title}</p>
      </div>
      {Array.isArray(items) && items.length > 0 ? (
        <ul className="space-y-2 text-sm leading-6 text-slate-700">
          {items.map((item, index) => (
            <li key={index}>- {typeof item === "object" ? JSON.stringify(item) : item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">{emptyLabel}</p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Timeline & Resource Tab                                            */
/* ------------------------------------------------------------------ */

function TimelineTab({ proposal }: { proposal: ProposalData }) {
  const timeline = proposal.timeline ?? {};
  const resource = proposal.resource_plan ?? {};
  const phases = Array.isArray(timeline.phases) ? timeline.phases : [];
  const teamMembers = Array.isArray(resource.team_members) ? resource.team_members : [];

  return (
    <div className="space-y-8">
      {/* Timeline */}
      <div>
        <SectionHeader
          title="일정 계획"
          description={timeline.total_duration ? `전체 기간: ${timeline.total_duration}` : undefined}
        />
        {phases.length > 0 ? (
          <div className="space-y-3">
            {phases.map((phase, index) => (
              <div key={index} className="list-card" style={{ borderLeft: `3px solid ${PROPOSAL_ACCENT}` }}>
                <div className="flex items-start gap-4">
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white"
                    style={{ background: PROPOSAL_ACCENT }}
                  >
                    {index + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="text-base font-bold tracking-[-0.03em] text-slate-900">{typeof phase.name === "object" ? JSON.stringify(phase.name) : (phase.name ?? "")}</p>
                      <span className="pill-badge bg-[#D9730D]/10 text-[#D9730D]">
                        <Calendar className="mr-1 inline-block h-3 w-3" />{typeof phase.duration === "object" ? JSON.stringify(phase.duration) : (phase.duration ?? "")}
                      </span>
                    </div>
                    {Array.isArray(phase.deliverables) && phase.deliverables.length > 0 ? (
                      <div className="mt-3">
                        <p className="data-label">산출물</p>
                        <ul className="mt-2 space-y-1 text-sm leading-6 text-slate-700">
                          {phase.deliverables.map((d, i) => (
                            <li key={i}>- {typeof d === "object" ? JSON.stringify(d) : d}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanel title="일정 계획이 없습니다" />
        )}
      </div>

      {/* Resource Plan */}
      <div>
        <SectionHeader
          title="리소스 계획"
          description={resource.total_man_months != null ? `총 ${resource.total_man_months} M/M` : undefined}
        />
        {teamMembers.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left">
                  <th className="px-4 py-3 font-semibold text-slate-900">역할</th>
                  <th className="px-4 py-3 font-semibold text-slate-900">인원</th>
                  <th className="px-4 py-3 font-semibold text-slate-900">담당 업무</th>
                </tr>
              </thead>
              <tbody>
                {teamMembers.map((member, index) => (
                  <tr key={index} className="border-b border-slate-100">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4" style={{ color: PROPOSAL_ACCENT }} />
                        <span className="font-medium text-slate-900">{typeof member.role === "object" ? JSON.stringify(member.role) : (member.role ?? "")}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="pill-badge bg-[#D9730D]/10 text-[#D9730D] font-semibold">{member.count != null ? member.count : 0}명</span>
                    </td>
                    <td className="px-4 py-3">
                      {Array.isArray(member.responsibilities) && member.responsibilities.length > 0 ? (
                        <ul className="space-y-1 text-slate-600">
                          {member.responsibilities.map((resp, i) => (
                            <li key={i}>- {typeof resp === "object" ? JSON.stringify(resp) : resp}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyPanel title="리소스 계획이 없습니다" />
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Risk Tab                                                           */
/* ------------------------------------------------------------------ */

function RiskTab({ risks }: { risks: Risk[] }) {
  if (!Array.isArray(risks) || !risks.length) {
    return (
      <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
        <CheckCircle2 className="h-10 w-10 text-[#0F7B6C]" />
        <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">식별된 리스크가 없습니다</p>
      </div>
    );
  }

  const grouped: Record<string, Risk[]> = { HIGH: [], MEDIUM: [], LOW: [] };
  for (const risk of risks) {
    const level = risk.level?.toUpperCase() ?? "MEDIUM";
    if (!grouped[level]) grouped[level] = [];
    grouped[level].push(risk);
  }

  return (
    <div className="space-y-8">
      <SectionHeader title="리스크 현황" description={`총 ${risks.length}건의 리스크가 식별되었습니다`} />

      {/* Summary bar */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="list-card" style={{ borderLeft: "3px solid #E03E3E" }}>
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-rose-600" />
            <p className="data-label">고위험</p>
          </div>
          <p className="mt-2 text-2xl font-extrabold text-slate-900">{grouped.HIGH?.length ?? 0}</p>
        </div>
        <div className="list-card" style={{ borderLeft: "3px solid #D9730D" }}>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <p className="data-label">중위험</p>
          </div>
          <p className="mt-2 text-2xl font-extrabold text-slate-900">{grouped.MEDIUM?.length ?? 0}</p>
        </div>
        <div className="list-card" style={{ borderLeft: "3px solid #0F7B6C" }}>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <p className="data-label">저위험</p>
          </div>
          <p className="mt-2 text-2xl font-extrabold text-slate-900">{grouped.LOW?.length ?? 0}</p>
        </div>
      </div>

      {/* Risk cards */}
      <div className="space-y-3">
        {(Array.isArray(risks) ? risks : []).map((risk, index) => {
          const levelKey = risk.level?.toUpperCase() ?? "MEDIUM";
          const levelStyle = RISK_LEVEL_STYLE[levelKey] ?? RISK_LEVEL_STYLE.MEDIUM;
          const levelLabel = RISK_LEVEL_LABEL[levelKey] ?? risk.level;

          return (
            <div key={index} className="list-card">
              <div className="flex items-start gap-4">
                <div className="mt-0.5">
                  {levelKey === "HIGH" ? (
                    <ShieldAlert className="h-5 w-5 text-rose-600" />
                  ) : levelKey === "MEDIUM" ? (
                    <AlertTriangle className="h-5 w-5 text-amber-600" />
                  ) : (
                    <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`pill-badge font-semibold ${levelStyle}`}>{levelLabel}</span>
                  </div>
                  <p className="mt-2 text-base font-semibold text-slate-900">{typeof risk.description === "object" ? JSON.stringify(risk.description) : (risk.description || "")}</p>
                  <div className="mt-4 grid gap-4 lg:grid-cols-2">
                    <div className="surface-muted p-4">
                      <p className="data-label">영향</p>
                      <p className="mt-2 text-sm leading-7 text-slate-700">{typeof risk.impact === "object" ? JSON.stringify(risk.impact) : (risk.impact || "-")}</p>
                    </div>
                    <div className="surface-muted p-4">
                      <p className="data-label">대응 방안</p>
                      <p className="mt-2 text-sm leading-7 text-slate-700">{typeof risk.mitigation === "object" ? JSON.stringify(risk.mitigation) : (risk.mitigation || "-")}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
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
