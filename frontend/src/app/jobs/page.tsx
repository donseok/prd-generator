"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowLeft,
  Layers,
  Clock,
  Loader2,
  AlertCircle,
  XCircle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Play,
} from "lucide-react";
import { api, ProcessingJob } from "@/lib/api";

const ITEMS_PER_PAGE = 10;

export default function JobsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);

  const { data, isLoading, error } = useQuery({
    queryKey: ["jobs", page],
    queryFn: () => api.listJobs(page * ITEMS_PER_PAGE, ITEMS_PER_PAGE),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const cancelMutation = useMutation({
    mutationFn: (jobId: string) => api.cancelProcessing(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const handleCancel = async (jobId: string) => {
    if (confirm("이 작업을 취소하시겠습니까?")) {
      cancelMutation.mutate(jobId);
    }
  };

  const jobs = data?.jobs || [];
  const totalCount = data?.total || 0;
  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-lg">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-lg font-bold">작업 히스토리</h1>
                  <p className="text-xs text-slate-400">
                    총 {totalCount}개의 작업
                  </p>
                </div>
              </div>
            </div>

            <Link
              href="/upload"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            >
              <Play className="w-4 h-4" />
              새 작업 시작
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-yellow-400" />
            <p className="text-slate-400">작업 목록 로딩 중...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
            <p className="text-red-400">작업 목록을 불러올 수 없습니다</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="w-12 h-12 mx-auto mb-4 text-slate-500" />
            <p className="text-slate-400 mb-4">진행된 작업이 없습니다</p>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            >
              첫 작업 시작하기
            </Link>
          </div>
        ) : (
          <>
            {/* Jobs List */}
            <div className="space-y-3">
              {jobs.map((job) => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  onCancel={() => handleCancel(job.job_id)}
                  isCanceling={cancelMutation.isPending}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-4">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="flex items-center gap-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                  이전
                </button>
                <span className="text-sm text-slate-400">
                  {page + 1} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="flex items-center gap-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  다음
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function JobCard({
  job,
  onCancel,
  isCanceling,
}: {
  job: ProcessingJob;
  onCancel: () => void;
  isCanceling: boolean;
}) {
  const getJobLink = () => {
    if (job.requires_pm_review) {
      return `/review/${job.job_id}`;
    }
    if (job.prd_id) {
      return `/prd/${job.prd_id}`;
    }
    return `/processing/${job.job_id}`;
  };

  const statusConfig: Record<
    string,
    { label: string; color: string; icon: React.ReactNode }
  > = {
    pending: {
      label: "대기",
      color: "text-slate-400 bg-slate-500/20",
      icon: <Clock className="w-4 h-4" />,
    },
    parsing: {
      label: "파싱 중",
      color: "text-blue-400 bg-blue-500/20",
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
    },
    normalizing: {
      label: "정규화 중",
      color: "text-purple-400 bg-purple-500/20",
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
    },
    validating: {
      label: "검증 중",
      color: "text-amber-400 bg-amber-500/20",
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
    },
    generating: {
      label: "생성 중",
      color: "text-emerald-400 bg-emerald-500/20",
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
    },
    pm_review: {
      label: "PM 검토",
      color: "text-orange-400 bg-orange-500/20",
      icon: <AlertCircle className="w-4 h-4" />,
    },
    completed: {
      label: "완료",
      color: "text-green-400 bg-green-500/20",
      icon: <CheckCircle className="w-4 h-4" />,
    },
    failed: {
      label: "실패",
      color: "text-red-400 bg-red-500/20",
      icon: <XCircle className="w-4 h-4" />,
    },
  };

  const statusInfo = statusConfig[job.status] || statusConfig.pending;
  const isProcessing = ["parsing", "normalizing", "validating", "generating"].includes(
    job.status
  );

  return (
    <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex items-start justify-between">
        <Link href={getJobLink()} className="flex-1 group">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${statusInfo.color}`}
            >
              {statusInfo.icon}
              {statusInfo.label}
            </span>
            {job.requires_pm_review && job.status !== "pm_review" && (
              <span className="px-2 py-1 rounded text-xs font-medium text-orange-400 bg-orange-500/20">
                검토 필요
              </span>
            )}
          </div>
          <h3 className="font-medium text-sm group-hover:text-blue-400 transition-colors">
            {job.documents?.join(", ") || job.job_id}
          </h3>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
            <span>ID: {job.job_id.slice(0, 8)}...</span>
            <span>·</span>
            <span>
              {new Date(job.created_at).toLocaleString("ko-KR", {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        </Link>

        <div className="flex items-center gap-2 ml-4">
          {job.prd_id && (
            <Link
              href={`/prd/${job.prd_id}`}
              className="px-3 py-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded-lg text-sm transition-colors"
            >
              PRD 보기
            </Link>
          )}

          {isProcessing && (
            <button
              onClick={onCancel}
              disabled={isCanceling}
              className="px-3 py-1.5 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              취소
            </button>
          )}

          {job.requires_pm_review && job.status === "pm_review" && (
            <Link
              href={`/review/${job.job_id}`}
              className="px-3 py-1.5 bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 rounded-lg text-sm transition-colors"
            >
              검토하기
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
