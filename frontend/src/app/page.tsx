"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  Upload,
  Clock,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const { data: prds } = useQuery({
    queryKey: ["prds"],
    queryFn: () => api.listPRDs(0, 5),
  });

  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(0, 5),
  });

  const recentPRDs = prds?.prds || [];
  const recentJobs = jobs?.jobs || [];
  const pendingReviews = recentJobs.filter((j) => j.requires_pm_review).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg">
                <Layers className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold">PRD 자동 생성 시스템</h1>
                <p className="text-xs text-slate-400">4단계 AI 파이프라인</p>
              </div>
            </div>
            <Link
              href="/upload"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span>새 PRD 생성</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<FileText className="w-5 h-5" />}
            label="총 PRD"
            value={prds?.total || 0}
            color="blue"
          />
          <StatCard
            icon={<Clock className="w-5 h-5" />}
            label="처리 중"
            value={recentJobs.filter((j) => j.status === "processing").length}
            color="yellow"
          />
          <StatCard
            icon={<AlertCircle className="w-5 h-5" />}
            label="검토 대기"
            value={pendingReviews}
            color="orange"
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="완료"
            value={recentJobs.filter((j) => j.status === "completed").length}
            color="green"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent PRDs */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">최근 PRD</h2>
              <Link
                href="/history"
                className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                전체 보기 <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {recentPRDs.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>아직 생성된 PRD가 없습니다</p>
                <Link
                  href="/upload"
                  className="text-blue-400 hover:underline mt-2 inline-block"
                >
                  첫 PRD 만들기
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentPRDs.map((prd) => (
                  <Link
                    key={prd.id}
                    href={`/prd/${prd.id}`}
                    className="block p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium">{prd.title}</h3>
                        <p className="text-sm text-slate-400 mt-1">
                          요구사항 {prd.requirements_count}개
                        </p>
                      </div>
                      <ConfidenceBadge score={prd.overall_confidence} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Recent Jobs */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">최근 작업</h2>
              <Link
                href="/jobs"
                className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                전체 보기 <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {recentJobs.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>진행 중인 작업이 없습니다</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentJobs.map((job) => (
                  <Link
                    key={job.job_id}
                    href={
                      job.requires_pm_review
                        ? `/review/${job.job_id}`
                        : job.prd_id
                        ? `/prd/${job.prd_id}`
                        : `/processing/${job.job_id}`
                    }
                    className="block p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium">
                          {job.documents?.join(", ") || job.job_id}
                        </h3>
                        <p className="text-sm text-slate-400 mt-1">
                          {new Date(job.created_at).toLocaleDateString("ko-KR")}
                        </p>
                      </div>
                      <StatusBadge status={job.status} needsReview={job.requires_pm_review} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Pipeline Overview */}
        <div className="mt-8 bg-slate-800/50 rounded-xl border border-slate-700 p-6">
          <h2 className="text-lg font-semibold mb-4">파이프라인 구조</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { name: "Layer 1", subtitle: "파싱", color: "blue", desc: "파일 형식별 텍스트 추출" },
              { name: "Layer 2", subtitle: "정규화", color: "purple", desc: "요구사항 분류 및 변환", highlight: true },
              { name: "Layer 3", subtitle: "검증", color: "amber", desc: "품질 검증 및 PM 검토" },
              { name: "Layer 4", subtitle: "생성", color: "emerald", desc: "PRD 문서 자동 생성" },
            ].map((layer, i) => (
              <div
                key={layer.name}
                className={`p-4 rounded-lg border ${
                  layer.highlight
                    ? "border-purple-500/50 bg-purple-500/10"
                    : "border-slate-600 bg-slate-700/30"
                }`}
              >
                <div className={`text-${layer.color}-400 font-semibold`}>
                  {layer.name}
                </div>
                <div className="text-sm text-slate-300">{layer.subtitle}</div>
                <div className="text-xs text-slate-400 mt-2">{layer.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: "blue" | "yellow" | "orange" | "green";
}) {
  const colors = {
    blue: "from-blue-500/20 to-blue-600/20 border-blue-500/30",
    yellow: "from-yellow-500/20 to-yellow-600/20 border-yellow-500/30",
    orange: "from-orange-500/20 to-orange-600/20 border-orange-500/30",
    green: "from-green-500/20 to-green-600/20 border-green-500/30",
  };

  return (
    <div
      className={`p-4 rounded-xl bg-gradient-to-br ${colors[color]} border`}
    >
      <div className="flex items-center gap-3">
        <div className="text-slate-300">{icon}</div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm text-slate-400">{label}</div>
        </div>
      </div>
    </div>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  const percent = Math.round(score * 100);
  const color =
    percent >= 80
      ? "bg-green-500/20 text-green-400"
      : percent >= 60
      ? "bg-yellow-500/20 text-yellow-400"
      : "bg-red-500/20 text-red-400";

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${color}`}>
      {percent}%
    </span>
  );
}

function StatusBadge({ status, needsReview }: { status: string; needsReview?: boolean }) {
  if (needsReview) {
    return (
      <span className="px-2 py-1 rounded text-xs font-medium bg-orange-500/20 text-orange-400">
        검토 필요
      </span>
    );
  }

  const statusConfig: Record<string, { color: string; label: string }> = {
    pending: { color: "bg-slate-500/20 text-slate-400", label: "대기" },
    parsing: { color: "bg-blue-500/20 text-blue-400", label: "파싱 중" },
    normalizing: { color: "bg-purple-500/20 text-purple-400", label: "정규화 중" },
    validating: { color: "bg-amber-500/20 text-amber-400", label: "검증 중" },
    generating: { color: "bg-emerald-500/20 text-emerald-400", label: "생성 중" },
    completed: { color: "bg-green-500/20 text-green-400", label: "완료" },
    failed: { color: "bg-red-500/20 text-red-400", label: "실패" },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  );
}
