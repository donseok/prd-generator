"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowLeft,
  Layers,
  AlertCircle,
  CheckCircle,
  XCircle,
  Edit3,
  Loader2,
  ChevronDown,
  ChevronUp,
  Send,
  FileText,
} from "lucide-react";
import { api, ReviewItem } from "@/lib/api";

type Decision = "approve" | "reject" | "modify";

interface ReviewDecision {
  itemId: string;
  decision: Decision;
  notes?: string;
  modifiedContent?: Record<string, unknown>;
}

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
    mutationFn: async (decision: ReviewDecision) => {
      return api.submitReviewDecision(
        jobId,
        decision.itemId,
        decision.decision,
        decision.notes,
        decision.modifiedContent
      );
    },
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

  const setDecision = (itemId: string, decision: Decision, notes?: string) => {
    const newDecisions = new Map(decisions);
    newDecisions.set(itemId, { itemId, decision, notes });
    setDecisions(newDecisions);
  };

  const handleSubmitAll = async () => {
    if (decisions.size === 0) return;

    setSubmitting(true);
    try {
      // Submit all decisions
      for (const decision of decisions.values()) {
        await submitDecisionMutation.mutateAsync(decision);
      }
      setDecisions(new Map());
    } catch (err) {
      console.error("Failed to submit decisions:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCompleteReview = async () => {
    if (reviewData && reviewData.pending_count > 0) {
      alert("모든 항목을 검토해야 합니다.");
      return;
    }
    completeReviewMutation.mutate();
  };

  const pendingItems = reviewData?.pending_items || [];
  const resolvedCount = reviewData?.resolved_items?.length || 0;
  const totalCount = pendingItems.length + resolvedCount;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-orange-500 to-amber-500 rounded-lg">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-lg font-bold">PM 검토</h1>
                  <p className="text-xs text-slate-400">
                    {resolvedCount}/{totalCount} 완료
                  </p>
                </div>
              </div>
            </div>

            {pendingItems.length === 0 && resolvedCount > 0 && (
              <button
                onClick={handleCompleteReview}
                disabled={completeReviewMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg transition-colors disabled:opacity-50"
              >
                {completeReviewMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <CheckCircle className="w-4 h-4" />
                )}
                검토 완료
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-orange-400" />
            <p className="text-slate-400">검토 항목 로딩 중...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
            <p className="text-red-400">검토 항목을 불러올 수 없습니다</p>
          </div>
        ) : pendingItems.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-400" />
            <p className="text-xl font-semibold text-green-400 mb-2">
              모든 검토가 완료되었습니다
            </p>
            <p className="text-slate-400 mb-6">
              PRD 생성을 완료하려면 상단의 &quot;검토 완료&quot; 버튼을 클릭하세요.
            </p>
            <button
              onClick={handleCompleteReview}
              disabled={completeReviewMutation.isPending}
              className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-500 rounded-lg transition-colors disabled:opacity-50"
            >
              {completeReviewMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <FileText className="w-5 h-5" />
              )}
              PRD 생성 완료
            </button>
          </div>
        ) : (
          <>
            {/* Instructions */}
            <div className="mb-6 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg">
              <h3 className="font-medium text-orange-400 mb-2">검토 안내</h3>
              <p className="text-sm text-slate-300">
                아래 항목들은 신뢰도가 80% 미만이거나 추가 확인이 필요한 요구사항입니다.
                각 항목을 검토하고 승인, 거부, 또는 수정 결정을 내려주세요.
              </p>
            </div>

            {/* Pending Items */}
            <div className="space-y-4">
              {pendingItems.map((item) => (
                <ReviewItemCard
                  key={item.id}
                  item={item}
                  expanded={expandedItem === item.id}
                  onToggle={() =>
                    setExpandedItem(expandedItem === item.id ? null : item.id)
                  }
                  decision={decisions.get(item.id)}
                  onDecision={(decision, notes) =>
                    setDecision(item.id, decision, notes)
                  }
                />
              ))}
            </div>

            {/* Submit Button */}
            {decisions.size > 0 && (
              <div className="mt-8 flex justify-end">
                <button
                  onClick={handleSubmitAll}
                  disabled={submitting}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors disabled:opacity-50"
                >
                  {submitting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                  결정 제출 ({decisions.size}개)
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
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
  const [notes, setNotes] = useState("");

  const issueTypeLabels: Record<string, { label: string; color: string }> = {
    low_confidence: { label: "낮은 신뢰도", color: "text-yellow-400" },
    ambiguous: { label: "모호함", color: "text-orange-400" },
    incomplete: { label: "불완전", color: "text-red-400" },
    conflict: { label: "충돌", color: "text-purple-400" },
    missing_info: { label: "정보 부족", color: "text-blue-400" },
  };

  const issueInfo = issueTypeLabels[item.issue_type] || {
    label: item.issue_type,
    color: "text-slate-400",
  };

  return (
    <div
      className={`rounded-xl border transition-all ${
        decision
          ? decision.decision === "approve"
            ? "border-green-500/50 bg-green-500/10"
            : decision.decision === "reject"
            ? "border-red-500/50 bg-red-500/10"
            : "border-blue-500/50 bg-blue-500/10"
          : "border-slate-700 bg-slate-800/50"
      }`}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-start justify-between text-left"
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium bg-slate-700 ${issueInfo.color}`}
            >
              {issueInfo.label}
            </span>
            <span className="text-xs text-slate-500">{item.requirement_id}</span>
          </div>
          <p className="font-medium">{item.description}</p>
        </div>
        <div className="ml-4 flex items-center gap-2">
          {decision && (
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                decision.decision === "approve"
                  ? "bg-green-500/20 text-green-400"
                  : decision.decision === "reject"
                  ? "bg-red-500/20 text-red-400"
                  : "bg-blue-500/20 text-blue-400"
              }`}
            >
              {decision.decision === "approve"
                ? "승인"
                : decision.decision === "reject"
                ? "거부"
                : "수정"}
            </span>
          )}
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-700">
          {/* Original Text */}
          <div className="mt-4">
            <h4 className="text-sm font-medium text-slate-300 mb-2">원본 텍스트</h4>
            <div className="p-3 bg-slate-900/50 rounded-lg text-sm text-slate-400">
              {item.original_text}
            </div>
          </div>

          {/* Suggested Resolution */}
          {item.suggested_resolution && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-slate-300 mb-2">
                제안된 해결책
              </h4>
              <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-sm text-blue-300">
                {item.suggested_resolution}
              </div>
            </div>
          )}

          {/* Notes Input */}
          <div className="mt-4">
            <label className="text-sm font-medium text-slate-300 mb-2 block">
              메모 (선택사항)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="결정에 대한 메모를 입력하세요..."
              className="w-full p-3 bg-slate-900/50 border border-slate-600 rounded-lg text-sm resize-none focus:outline-none focus:border-blue-500"
              rows={2}
            />
          </div>

          {/* Decision Buttons */}
          <div className="mt-4 flex gap-3">
            <button
              onClick={() => onDecision("approve", notes)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                decision?.decision === "approve"
                  ? "bg-green-600 text-white"
                  : "bg-slate-700 hover:bg-green-600/50 text-slate-300"
              }`}
            >
              <CheckCircle className="w-4 h-4" />
              승인
            </button>
            <button
              onClick={() => onDecision("reject", notes)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                decision?.decision === "reject"
                  ? "bg-red-600 text-white"
                  : "bg-slate-700 hover:bg-red-600/50 text-slate-300"
              }`}
            >
              <XCircle className="w-4 h-4" />
              거부
            </button>
            <button
              onClick={() => onDecision("modify", notes)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                decision?.decision === "modify"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 hover:bg-blue-600/50 text-slate-300"
              }`}
            >
              <Edit3 className="w-4 h-4" />
              수정
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
