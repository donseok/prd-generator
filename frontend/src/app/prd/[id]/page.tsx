"use client";

import { useMemo, useState, type ReactNode } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { AlertCircle, CheckCircle2, ChevronDown, ChevronRight, Download, Flag, Lock, Shield, Target, Users } from "lucide-react";
import { api, type Requirement } from "@/lib/api";
import { AppShell, HeroPanel, MetricCard, SectionHeader, TopBar, formatDate, scoreBadge } from "@/components/app-shell";

type TabKey = "overview" | "requirements" | "milestones" | "unresolved";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "overview", label: "개요" },
  { key: "requirements", label: "요구사항" },
  { key: "milestones", label: "마일스톤" },
  { key: "unresolved", label: "미해결 이슈" },
];

const PRIORITY_STYLE: Record<string, string> = {
  HIGH: "bg-gradient-to-r from-rose-100 to-rose-50 text-rose-700",
  MEDIUM: "bg-gradient-to-r from-amber-100 to-amber-50 text-amber-700",
  LOW: "bg-slate-100 text-slate-600",
};

const INFO_TILE_ACCENTS = [
  "from-[#6366F1] to-[#818CF8]",
  "from-[#8B5CF6] to-[#A78BFA]",
  "from-[#F59E0B] to-[#FBBF24]",
  "from-[#10B981] to-[#34D399]",
];

export default function PRDViewerPage() {
  const params = useParams();
  const prdId = params.id as string;
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [expandedReqs, setExpandedReqs] = useState<Set<string>>(new Set());

  const { data: prd, isLoading, error } = useQuery({
    queryKey: ["prd", prdId],
    queryFn: () => api.getPRD(prdId),
  });

  const allRequirements = useMemo(() => {
    if (!prd) return [];
    return [...prd.functional_requirements, ...prd.non_functional_requirements, ...prd.constraints];
  }, [prd]);

  async function handleExport(format: "markdown" | "json" | "html") {
    const data = await api.exportPRD(prdId, format);
    const blob = new Blob([typeof data === "string" ? data : JSON.stringify(data, null, 2)], {
      type: format === "json" ? "application/json" : "text/plain",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${prd?.title ?? "prd"}.${format === "markdown" ? "md" : format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function toggleReq(id: string) {
    setExpandedReqs((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (isLoading) {
    return (
      <AppShell header={<TopBar title="PRD 상세" subtitle="문서를 불러오는 중입니다" href="/history" />}>
        <section className="section-card flex items-center justify-center py-20">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#6366F1]/30 border-t-[#6366F1]" />
        </section>
      </AppShell>
    );
  }

  if (error || !prd) {
    return (
      <AppShell header={<TopBar title="PRD 상세" subtitle="문서를 찾을 수 없습니다" href="/history" />}>
        <section className="section-card">
          <div className="flex flex-col items-center justify-center px-6 py-20 text-center">
            <AlertCircle className="h-10 w-10 text-[#F43F5E]" />
            <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">PRD를 불러오지 못했습니다</p>
            <Link href="/history" className="mt-6 brand-button">
              아카이브로 돌아가기
            </Link>
          </div>
        </section>
      </AppShell>
    );
  }

  const confidence = scoreBadge(prd.metadata.overall_confidence);

  return (
    <AppShell
      header={
        <TopBar
          title={prd.title}
          subtitle={`버전 ${prd.metadata.version} · ${formatDate(prd.metadata.created_at)}`}
          href="/history"
          action={
            <div className="flex flex-wrap gap-2">
              <button onClick={() => handleExport("markdown")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Download className="h-4 w-4" />
                MD
              </button>
              <button onClick={() => handleExport("json")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Download className="h-4 w-4" />
                JSON
              </button>
              <button onClick={() => handleExport("html")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Download className="h-4 w-4" />
                HTML
              </button>
            </div>
          }
        />
      }
    >
      <HeroPanel
        kicker="문서 리더"
        title={prd.title}
        description="개요부터 요구사항, 마일스톤, 미해결 이슈까지 한 흐름으로 읽을 수 있게 문서형 화면으로 다시 구성했습니다. 중요한 메타 정보는 우측 패널에 모아두고, 세부 내용은 탭 기반으로 정리했습니다."
        aside={
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <span className={`pill-badge ${confidence.className}`}>신뢰도 {confidence.label}</span>
              <span className="pill-badge bg-slate-100 text-slate-600">{prd.metadata.status}</span>
              {prd.metadata.requires_pm_review ? (
                <span className="pill-badge bg-amber-100 text-amber-700">PM 검토 필요</span>
              ) : (
                <span className="pill-badge bg-emerald-100 text-emerald-700">즉시 사용 가능</span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <InfoTile label="기능 요구사항" value={prd.functional_requirements.length} index={0} />
              <InfoTile label="비기능 요구사항" value={prd.non_functional_requirements.length} index={1} />
              <InfoTile label="제약 조건" value={prd.constraints.length} index={2} />
              <InfoTile label="마일스톤" value={prd.milestones.length} index={3} />
            </div>
          </div>
        }
      />

      <section className="grid gap-4 lg:grid-cols-4">
        <MetricCard label="총 요구사항" value={allRequirements.length} note="기능, 비기능, 제약 조건 합계" />
        <MetricCard label="미해결 이슈" value={prd.unresolved_items.length} note="추가 검토가 필요한 항목" accent="warm" />
        <MetricCard label="목표 수" value={prd.overview.goals.length} note="문서에 정의된 핵심 목표" accent="mint" />
        <MetricCard label="대상 사용자" value={prd.overview.target_users.length} note="핵심 사용자 세그먼트" />
      </section>

      <section className="section-card">
        <div className="mb-6 flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`tab-button ${activeTab === tab.key ? "tab-button-active" : "tab-button-idle"}`}>
              {tab.label}
              {tab.key === "requirements" ? ` (${allRequirements.length})` : ""}
              {tab.key === "milestones" ? ` (${prd.milestones.length})` : ""}
              {tab.key === "unresolved" ? ` (${prd.unresolved_items.length})` : ""}
            </button>
          ))}
        </div>

        {activeTab === "overview" ? <OverviewTab prd={prd} /> : null}
        {activeTab === "requirements" ? <RequirementsTab prd={prd} expandedReqs={expandedReqs} onToggle={toggleReq} /> : null}
        {activeTab === "milestones" ? <MilestonesTab prd={prd} /> : null}
        {activeTab === "unresolved" ? <UnresolvedTab prd={prd} /> : null}
      </section>
    </AppShell>
  );
}

function InfoTile({ label, value, index = 0 }: { label: string; value: number; index?: number }) {
  const accent = INFO_TILE_ACCENTS[index % INFO_TILE_ACCENTS.length];

  return (
    <div className="surface-muted relative overflow-hidden px-4 py-3">
      <div className={`absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r ${accent}`} />
      <p className="data-label">{label}</p>
      <p className="mt-2 text-xl font-bold tracking-tight text-slate-900">{value}</p>
    </div>
  );
}

function OverviewTab({ prd }: { prd: Awaited<ReturnType<typeof api.getPRD>> }) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="space-y-6">
        <ReadingBlock title="배경">{prd.overview.background}</ReadingBlock>
        <ReadingBlock title="범위">{prd.overview.scope}</ReadingBlock>
        {prd.overview.out_of_scope.length ? <ReadingListBlock title="범위 외 항목" items={prd.overview.out_of_scope} /> : null}
      </div>

      <aside className="space-y-4">
        <CompactInfoBlock title="목표" icon={<Target className="h-4 w-4 text-[#6366F1]" />} items={prd.overview.goals} emptyLabel="등록된 목표가 없습니다." />
        <CompactInfoBlock title="대상 사용자" icon={<Users className="h-4 w-4 text-[#8B5CF6]" />} items={prd.overview.target_users} emptyLabel="등록된 대상 사용자가 없습니다." />
        <CompactInfoBlock title="성공 지표" icon={<Flag className="h-4 w-4 text-[#10B981]" />} items={prd.overview.success_metrics} emptyLabel="등록된 성공 지표가 없습니다." />
      </aside>
    </div>
  );
}

function RequirementsTab({
  prd,
  expandedReqs,
  onToggle,
}: {
  prd: Awaited<ReturnType<typeof api.getPRD>>;
  expandedReqs: Set<string>;
  onToggle: (id: string) => void;
}) {
  return (
    <div className="space-y-8">
      <RequirementGroup title="기능 요구사항" icon={<Target className="h-4 w-4 text-[#6366F1]" />}>
        {prd.functional_requirements.map((req) => (
          <RequirementCard key={req.id} req={req} expanded={expandedReqs.has(req.id)} onToggle={() => onToggle(req.id)} />
        ))}
      </RequirementGroup>
      <RequirementGroup title="비기능 요구사항" icon={<Shield className="h-4 w-4 text-[#8B5CF6]" />}>
        {prd.non_functional_requirements.map((req) => (
          <RequirementCard key={req.id} req={req} expanded={expandedReqs.has(req.id)} onToggle={() => onToggle(req.id)} />
        ))}
      </RequirementGroup>
      <RequirementGroup title="제약 조건" icon={<Lock className="h-4 w-4 text-[#F59E0B]" />}>
        {prd.constraints.map((req) => (
          <RequirementCard key={req.id} req={req} expanded={expandedReqs.has(req.id)} onToggle={() => onToggle(req.id)} />
        ))}
      </RequirementGroup>
    </div>
  );
}

function MilestonesTab({ prd }: { prd: Awaited<ReturnType<typeof api.getPRD>> }) {
  if (!prd.milestones.length) {
    return <EmptyPanel title="등록된 마일스톤이 없습니다" />;
  }

  return (
    <div className="grid gap-4">
      {prd.milestones
        .slice()
        .sort((a, b) => a.order - b.order)
        .map((milestone, index) => (
          <div key={milestone.id} className="list-card">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 text-base font-bold text-white">
                {index + 1}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-lg font-bold tracking-[-0.03em] text-slate-900">{milestone.name}</p>
                <p className="mt-2.5 text-sm leading-7 text-slate-600">{milestone.description}</p>
                {milestone.deliverables.length ? (
                  <div className="mt-4">
                    <p className="data-label">산출물</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
                      {milestone.deliverables.map((deliverable) => (
                        <li key={deliverable}>- {deliverable}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        ))}
    </div>
  );
}

function UnresolvedTab({ prd }: { prd: Awaited<ReturnType<typeof api.getPRD>> }) {
  if (!prd.unresolved_items.length) {
    return (
      <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
        <CheckCircle2 className="h-10 w-10 text-[#10B981]" />
        <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">미해결 이슈가 없습니다</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {prd.unresolved_items.map((item) => (
        <div key={item.id} className="list-card">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="pill-badge bg-slate-100 text-slate-600">{item.type}</span>
                <span className={`pill-badge ${PRIORITY_STYLE[item.priority] ?? PRIORITY_STYLE.MEDIUM}`}>{item.priority}</span>
              </div>
              <p className="mt-2.5 text-base font-semibold text-slate-900">{item.description}</p>
              {item.suggested_action ? <p className="mt-2 text-sm leading-6 text-slate-600">권장 조치: {item.suggested_action}</p> : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function RequirementGroup({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h3 className="text-base font-semibold tracking-tight text-slate-900">{title}</h3>
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function RequirementCard({
  req,
  expanded,
  onToggle,
}: {
  req: Requirement;
  expanded: boolean;
  onToggle: () => void;
}) {
  const confidence = scoreBadge(req.confidence_score);

  return (
    <div className="rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel)]">
      <button onClick={onToggle} className="flex w-full items-start gap-4 p-5 text-left">
        <div className="mt-1 text-slate-400">{expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}</div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="pill-badge bg-slate-100 text-slate-600">{req.id}</span>
            <span className={`pill-badge ${PRIORITY_STYLE[req.priority] ?? PRIORITY_STYLE.MEDIUM}`}>{req.priority}</span>
            <span className={`pill-badge ${confidence.className}`}>{confidence.label}</span>
          </div>
          <p className="mt-2.5 text-base font-semibold tracking-tight text-slate-900">{req.title}</p>
        </div>
      </button>

      {expanded ? (
        <div className="border-t border-[var(--line-soft)] px-5 pb-5 pl-14 pt-5">
          <div className="grid gap-4 lg:grid-cols-2">
            <DetailBlock title="설명">{req.description}</DetailBlock>
            <DetailBlock title="신뢰도 근거">{req.confidence_reason || "기록된 근거가 없습니다."}</DetailBlock>
            {req.user_story ? <DetailBlock title="사용자 스토리">{req.user_story}</DetailBlock> : null}
            <ListBlock title="인수 기준" items={req.acceptance_criteria} />
            <ListBlock title="가정 사항" items={req.assumptions} />
            <ListBlock title="누락 정보" items={req.missing_info} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ReadingBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="glass-panel-strong rounded-2xl p-6">
      <SectionHeader title={title} />
      <div className="text-sm leading-8 text-slate-700">{children}</div>
    </div>
  );
}

function ReadingListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="surface-muted p-5">
      <SectionHeader title={title} />
      <ul className="space-y-2 text-sm leading-7 text-slate-700">
        {items.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </div>
  );
}

function CompactInfoBlock({
  title,
  icon,
  items,
  emptyLabel,
}: {
  title: string;
  icon: ReactNode;
  items: string[];
  emptyLabel: string;
}) {
  return (
    <div className="surface-muted p-5">
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <p className="text-base font-semibold text-slate-900">{title}</p>
      </div>
      {items.length ? (
        <ul className="space-y-2 text-sm leading-6 text-slate-700">
          {items.map((item) => (
            <li key={item}>- {item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">{emptyLabel}</p>
      )}
    </div>
  );
}

function DetailBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="surface-muted p-4">
      <p className="data-label">{title}</p>
      <div className="mt-3 text-sm leading-7 text-slate-700">{children}</div>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="surface-muted p-4">
      <p className="data-label">{title}</p>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
          {items.map((item) => (
            <li key={item}>- {item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500">없음</p>
      )}
    </div>
  );
}

function EmptyPanel({ title }: { title: string }) {
  return (
    <div className="surface-muted flex items-center justify-center rounded-2xl px-6 py-16 text-center">
      <p className="text-base font-semibold text-slate-700">{title}</p>
    </div>
  );
}
