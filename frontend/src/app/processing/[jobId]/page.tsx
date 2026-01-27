"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowLeft,
  Layers,
  Settings,
  Zap,
  CheckCircle,
  Target,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";

const LAYERS = [
  { key: "parsing", name: "Layer 1: 파싱", icon: Settings, color: "blue" },
  { key: "normalizing", name: "Layer 2: 정규화", icon: Zap, color: "purple" },
  { key: "validating", name: "Layer 3: 검증", icon: CheckCircle, color: "amber" },
  { key: "generating", name: "Layer 4: 생성", icon: Target, color: "emerald" },
];

export default function ProcessingPage() {
  /**
   * 처리 상태 페이지 컴포넌트입니다.
   * AI 파이프라인의 실시간 진행률과 현재 단계를 보여줍니다.
   */
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  // 서버에서 작업 상태를 주기적으로 가져옵니다 (폴링)
  const { data: status, error } = useQuery({
    queryKey: ["processing", jobId],
    queryFn: () => api.getProcessingStatus(jobId),
    refetchInterval: (query) => {
      const data = query.state.data;
      // 완료되었거나, 실패했거나, 리뷰가 필요하면 폴링 중단
      if (data?.status === "completed" || data?.status === "failed" || data?.status === "pm_review") {
        return false;
      }
      return 2000; // 2초마다 갱신
    },
  });

  // 상태 변경에 따른 자동 이동
  useEffect(() => {
    if (status?.status === "completed" && status.prd_id) {
      // 완료되면 PRD 상세 페이지로 이동
      router.push(`/prd/${status.prd_id}`);
    } else if (status?.status === "pm_review") {
      // 검토가 필요하면 리뷰 페이지로 이동
      router.push(`/review/${jobId}`);
    }
  }, [status, jobId, router]);

  const currentLayerIndex = LAYERS.findIndex(
    (l) => l.key === status?.current_layer
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-lg font-bold">PRD 생성 중</h1>
                <p className="text-xs text-slate-400">{jobId}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        {error ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
            <p className="text-red-400">상태를 불러올 수 없습니다</p>
          </div>
        ) : !status ? (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-400" />
            <p className="text-slate-400">로딩 중...</p>
          </div>
        ) : status.status === "failed" ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
            <p className="text-xl font-semibold text-red-400 mb-2">처리 실패</p>
            <p className="text-slate-400">{status.error}</p>
            <Link
              href="/upload"
              className="inline-block mt-6 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg"
            >
              다시 시도
            </Link>
          </div>
        ) : (
          <>
            {/* 진행률 바 */}
            <div className="mb-12">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">진행률</span>
                <span className="text-white font-medium">{status.progress_percent}%</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500 transition-all duration-500"
                  style={{ width: `${status.progress_percent}%` }}
                />
              </div>
            </div>

            {/* 단계별 상태 시각화 */}
            <div className="space-y-4">
              {LAYERS.map((layer, index) => {
                const isComplete = index < currentLayerIndex || status.status === "completed";
                const isCurrent = index === currentLayerIndex && status.status !== "completed";
                const isPending = index > currentLayerIndex;

                const Icon = layer.icon;

                return (
                  <div
                    key={layer.key}
                    className={`
                      p-6 rounded-xl border transition-all
                      ${isComplete
                        ? "bg-slate-800/80 border-green-500/30"
                        : isCurrent
                        ? `bg-gradient-to-r from-${layer.color}-500/20 to-${layer.color}-600/20 border-${layer.color}-500/50 ring-2 ring-${layer.color}-500/30`
                        : "bg-slate-800/30 border-slate-700 opacity-50"
                      }
                    `}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`
                          p-3 rounded-lg
                          ${isComplete
                            ? "bg-green-500"
                            : isCurrent
                            ? `bg-${layer.color}-500`
                            : "bg-slate-700"
                          }
                        `}
                      >
                        {isComplete ? (
                          <CheckCircle className="w-6 h-6" />
                        ) : isCurrent ? (
                          <Loader2 className="w-6 h-6 animate-spin" />
                        ) : (
                          <Icon className="w-6 h-6" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold">{layer.name}</h3>
                        <p className="text-sm text-slate-400">
                          {isComplete
                            ? "완료"
                            : isCurrent
                            ? "처리 중..."
                            : "대기 중"}
                        </p>
                      </div>
                      {isComplete && (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* 처리 중인 문서 목록 */}
            <div className="mt-8 p-4 bg-slate-800/30 rounded-lg border border-slate-700">
              <h4 className="text-sm font-medium text-slate-300 mb-2">처리 중인 문서</h4>
              <div className="flex flex-wrap gap-2">
                {status.documents?.map((doc, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-slate-700 rounded-full text-sm"
                  >
                    {doc}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}