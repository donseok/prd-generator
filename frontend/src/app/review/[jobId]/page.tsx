"use client";

import { useMemo, useState, type ReactNode } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Edit3,
  FileText,
  Loader2,
  Send,
  XCircle,
} from "lucide-react";
import { api, type ReviewItem } from "@/lib/api";
import { AppShell, HeroPanel, MetricCard, SectionHeader, TopBar } from "@/components/app-shell";

type Decision = "approve" | "reject" | "modify";

interface ReviewDecision {
  itemId: string;
  decision: Decision;
  notes?: string;
  modifiedContent?: Record<string, unknown>;
}

const ISSUE_LABELS: Record<string, { label: string; tone: string }> = {
  low_confidence: { label: "낮은 신뢰도", tone: "bg-amber-100 text-amber-700" },
  ambiguous: { label: "모호한 표현", tone: "bg-orange-100 text-orange-700" },
  incomplete: { label: "불완전한 정보", tone: "bg-rose-100 text-rose-700" },
  conflict: { label: "충돌 가능성", tone: "bg-violet-100 text-violet-700" },
  missing_info: { label: "누락 정보", tone: "bg-sky-100 text-sky-700" },
};

export default function ReviewPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;
  const queryClient = useQueryClient();

  const [decisions, setDecisions] = useState<Map<string, ReviewDecision>>(new Map());
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { data: reviewData, isLoading, error } = useQuery({
    queryKey: ["review", jobId],
    queryFn: () => api.getPendingReviews(jobId),
  });

  const submitDecisionMutation = useMutation({
    mutationFn: async (decision: ReviewDecision) =>
      api.submitReviewDecision(jobId, decision.itemId, decision.decision, decision.notes, decision.modifiedContent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review", jobId] });
    },
  });

  const completeReviewMutation = useMutation({
    mutationFn: () => api.completeReview(jobId),
    onSuccess: (data) => {
      router.push(`/prd/${data.prd_id}`);
    },
  });

  const pendingItems = reviewData?.pending_items ?? [];
  const resolvedCount = reviewData?.resolved_items?.length ?? 0;
  const totalCount = pendingItems.length + resolvedCount;

  const completionRate = useMemo(() => {
    if (!totalCount) return 0;
    return Math.round((resolvedCount / totalCount) * 100);
  }, [resolvedCount, totalCount]);

  function setDecision(itemId: string, decision: Decision, notes?: string) {
    setDecisions((current) => {
      const next = new Map(current);
      next.set(itemId, { itemId, decision, notes });
      return next;
    });
  }

  async function handleSubmitAll() {
    if (!decisions.size) return;

    setSubmitting(true);
    try {
      for (const decision of Array.from(decisions.values())) {
        await submitDecisionMutation.mutateAsync(decision);
      }
      setDecisions(new Map());
    } catch (submitError) {
      console.error("리뷰 제출에 실패했습니다.", submitError);
    } finally {
      setSubmitting(false);
    }
  }

  function handleCompleteReview() {
    if (reviewData && reviewData.pending_count > 0) {
      alert("남아 있는 리뷰 항목을 먼저 처리해 주세요.");
      return;
    }
    completeReviewMutation.mutate();
  }

  return (
    <AppShell header={<TopBar title="PM 리뷰" subtitle={`${resolvedCount} / ${totalCount}개 처리`} href="/" />}>
      <HeroPanel
        kicker="사람 검토"
        title="판단이 필요한 요구사항을 집중 검토하는 단계입니다"
        description="애매하거나 신뢰도가 낮은 요구사항만 따로 모아 카드 단위로 검토할 수 있게 다시 구성했습니다. 승인, 반려, 수정 요청을 빠르게 선택하고 메모를 남긴 뒤 최종 PRD로 이어집니다."
        actions={
          pendingItems.length === 0 && resolvedCount > 0 ? (
            <button
              onClick={handleCompleteReview}
              disabled={completeReviewMutation.isPending}
              className="brand-button disabled:opacity-50"
            >
              {completeReviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              최종 PRD 열기
            </button>
          ) : null
        }
        aside={
          <div className="space-y-4">
            <div>
              <p className="data-label">완료율</p>
              <p className="mt-2 text-4xl font-semibold tracking-tight text-slate-900">{completionRate}%</p>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-slate-200">
              <div className="h-full rounded-full" style={{ width: `${completionRate}%`, background: "var(--gradient-warm)" }} />
            </div>
            <div className="surface-muted p-4">
              <p className="data-label">남은 항목</p>
              <p className="mt-2 text-sm font-medium text-slate-700">{pendingItems.length}개</p>
            </div>
          </div>
        }
      />

      <section className="grid gap-4 lg:grid-cols-3">
        <MetricCard label="총 리뷰 항목" value={totalCount} note="이번 작업에 포함된 전체 검토 수" />
        <MetricCard label="처리 완료" value={resolvedCount} note="이미 결정이 내려진 항목" accent="mint" />
        <MetricCard label="남은 검토" value={pendingItems.length} note="지금 판단이 필요한 항목" accent="warm" />
      </section>

      {isLoading ? (
        <FeedbackState
          icon={<Loader2 className="h-10 w-10 animate-spin text-slate-400" />}
          title="리뷰 항목을 불러오는 중입니다"
          description="리뷰 보드를 준비하고 있습니다."
        />
      ) : error ? (
        <FeedbackState
          icon={<AlertCircle className="h-10 w-10 text-rose-500" />}
          title="리뷰 항목을 불러오지 못했습니다"
          description="API 연결 상태를 확인한 뒤 다시 시도해 주세요."
        />
      ) : pendingItems.length === 0 ? (
        <FeedbackState
          icon={<CheckCircle2 className="h-10 w-10 text-emerald-600" />}
          title="검토할 항목이 없습니다"
          description="아래 버튼으로 리뷰를 종료하고 최종 PRD로 이동할 수 있습니다."
          action={
            <button
              onClick={handleCompleteReview}
              disabled={completeReviewMutation.isPending}
              className="brand-button disabled:opacity-50"
            >
              {completeReviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              리뷰 완료
            </button>
          }
        />
      ) : (
        <section className="section-card">
          <SectionHeader
            title="리뷰 보드"
            description="각 카드에서 원문과 제안 방향을 비교하고, 결정과 메모를 바로 남길 수 있습니다."
            action={
              decisions.size ? (
                <button onClick={handleSubmitAll} disabled={submitting} className="brand-button disabled:opacity-50">
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  결정 제출 ({decisions.size})
                </button>
              ) : null
            }
          />
          <div className="space-y-4">
            {pendingItems.map((item) => (
              <ReviewItemCard
                key={item.id}
                item={item}
                expanded={expandedItem === item.id}
                onToggle={() => setExpandedItem((current) => (current === item.id ? null : item.id))}
                decision={decisions.get(item.id)}
                onDecision={(decision, notes) => setDecision(item.id, decision, notes)}
              />
            ))}
          </div>
        </section>
      )}
    </AppShell>
  );
}

function FeedbackState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }) {
  return (
    <section className="section-card">
      <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
        {icon}
        <p className="mt-5 text-2xl font-semibold tracking-tight text-slate-900">{title}</p>
        <p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">{description}</p>
        {action ? <div className="mt-6">{action}</div> : null}
      </div>
    </section>
  );
}

function ReviewItemCard({
  item,
  expanded,
  onToggle,
  decision,
  onDecision,
}: {
  item: ReviewItem;
  expanded: boolean;
  onToggle: () => void;
  decision?: ReviewDecision;
  onDecision: (decision: Decision, notes?: string) => void;
}) {
  const [notes, setNotes] = useState(decision?.notes ?? "");
  const issue = ISSUE_LABELS[item.issue_type] ?? { label: item.issue_type, tone: "bg-slate-100 text-slate-600" };

  const decisionTone =
    decision?.decision === "approve"
      ? "border-emerald-200 bg-emerald-50"
      : decision?.decision === "reject"
      ? "border-rose-200 bg-rose-50"
      : decision?.decision === "modify"
      ? "border-blue-200 bg-blue-50"
      : "border-slate-200 bg-white/75";

  return (
    <div className={`rounded-[28px] border p-5 transition ${decisionTone}`}>
      <button onClick={onToggle} className="flex w-full items-start justify-between gap-4 text-left">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`pill-badge ${issue.tone}`}>{issue.label}</span>
            <span className="pill-badge bg-slate-100 text-slate-500">{item.requirement_id}</span>
          </div>
          <p className="mt-3 text-lg font-semibold tracking-tight text-slate-900">{item.description}</p>
        </div>
        <div className="flex items-center gap-3">
          {decision ? (
            <span
              className={`pill-badge ${
                decision.decision === "approve"
                  ? "bg-emerald-100 text-emerald-700"
                  : decision.decision === "reject"
                  ? "bg-rose-100 text-rose-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {decision.decision === "approve" ? "승인" : decision.decision === "reject" ? "반려" : "수정"}
            </span>
          ) : null}
          {expanded ? <ChevronUp className="h-5 w-5 text-slate-400" /> : <ChevronDown className="h-5 w-5 text-slate-400" />}
        </div>
      </button>

      {expanded ? (
        <div className="mt-5 border-t border-slate-200 pt-5">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="surface-muted p-4">
              <p className="data-label">원문</p>
              <p className="mt-3 text-sm leading-6 text-slate-700">{item.original_text}</p>
            </div>
            <div className="surface-muted p-4">
              <p className="data-label">권장 처리 방향</p>
              <p className="mt-3 text-sm leading-6 text-slate-700">{item.suggested_resolution ?? "제안된 처리 방향이 없습니다."}</p>
            </div>
          </div>

          <div className="mt-4">
            <label className="data-label">리뷰 메모</label>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
              placeholder="판단 근거나 수정 지시를 적어 주세요."
              className="input-surface mt-2 resize-none"
            />
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <DecisionButton active={decision?.decision === "approve"} tone="approve" icon={<CheckCircle2 className="h-4 w-4" />} label="승인" onClick={() => onDecision("approve", notes)} />
            <DecisionButton active={decision?.decision === "reject"} tone="reject" icon={<XCircle className="h-4 w-4" />} label="반려" onClick={() => onDecision("reject", notes)} />
            <DecisionButton active={decision?.decision === "modify"} tone="modify" icon={<Edit3 className="h-4 w-4" />} label="수정 요청" onClick={() => onDecision("modify", notes)} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function DecisionButton({
  active,
  tone,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  tone: "approve" | "reject" | "modify";
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  const toneClass =
    tone === "approve"
      ? active
        ? "bg-emerald-600 text-white"
        : "bg-emerald-50 text-emerald-700"
      : tone === "reject"
      ? active
        ? "bg-rose-600 text-white"
        : "bg-rose-50 text-rose-700"
      : active
      ? "bg-blue-600 text-white"
      : "bg-blue-50 text-blue-700";

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition hover:-translate-y-0.5 ${toneClass}`}
    >
      {icon}
      {label}
    </button>
  );
}
