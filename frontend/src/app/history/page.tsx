"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowLeft,
  Layers,
  FileText,
  Loader2,
  AlertCircle,
  Trash2,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { api, PRDListItem } from "@/lib/api";

const ITEMS_PER_PAGE = 10;

export default function HistoryPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["prds", page],
    queryFn: () => api.listPRDs(page * ITEMS_PER_PAGE, ITEMS_PER_PAGE),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deletePRD(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prds"] });
    },
  });

  const handleDelete = async (id: string, title: string) => {
    if (confirm(`"${title}" PRD를 삭제하시겠습니까?`)) {
      deleteMutation.mutate(id);
    }
  };

  const handleExport = async (id: string, format: "markdown" | "json" | "html") => {
    try {
      const content = await api.exportPRD(id, format);
      const blob = new Blob(
        [typeof content === "string" ? content : JSON.stringify(content, null, 2)],
        { type: format === "json" ? "application/json" : "text/plain" }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `prd-${id}.${format === "markdown" ? "md" : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
      alert("내보내기에 실패했습니다.");
    }
  };

  const prds = data?.prds || [];
  const totalCount = data?.total || 0;
  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

  // Filter by search query (client-side)
  const filteredPrds = searchQuery
    ? prds.filter((prd) =>
        prd.title.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : prds;

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
                <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-lg font-bold">PRD 히스토리</h1>
                  <p className="text-xs text-slate-400">
                    총 {totalCount}개의 PRD
                  </p>
                </div>
              </div>
            </div>

            <Link
              href="/upload"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            >
              <FileText className="w-4 h-4" />
              새 PRD 생성
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="PRD 제목으로 검색..."
              className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-400" />
            <p className="text-slate-400">PRD 목록 로딩 중...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
            <p className="text-red-400">PRD 목록을 불러올 수 없습니다</p>
          </div>
        ) : filteredPrds.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 mx-auto mb-4 text-slate-500" />
            <p className="text-slate-400 mb-4">
              {searchQuery ? "검색 결과가 없습니다" : "생성된 PRD가 없습니다"}
            </p>
            {!searchQuery && (
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
              >
                첫 PRD 만들기
              </Link>
            )}
          </div>
        ) : (
          <>
            {/* PRD List */}
            <div className="space-y-3">
              {filteredPrds.map((prd) => (
                <PRDCard
                  key={prd.id}
                  prd={prd}
                  onDelete={() => handleDelete(prd.id, prd.title)}
                  onExport={(format) => handleExport(prd.id, format)}
                  isDeleting={deleteMutation.isPending}
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

function PRDCard({
  prd,
  onDelete,
  onExport,
  isDeleting,
}: {
  prd: PRDListItem;
  onDelete: () => void;
  onExport: (format: "markdown" | "json" | "html") => void;
  isDeleting: boolean;
}) {
  const [showExportMenu, setShowExportMenu] = useState(false);

  const confidencePercent = Math.round(prd.overall_confidence * 100);
  const confidenceColor =
    confidencePercent >= 80
      ? "text-green-400 bg-green-500/20"
      : confidencePercent >= 60
      ? "text-yellow-400 bg-yellow-500/20"
      : "text-red-400 bg-red-500/20";

  const statusConfig: Record<string, { label: string; color: string }> = {
    draft: { label: "초안", color: "text-slate-400 bg-slate-500/20" },
    review: { label: "검토중", color: "text-orange-400 bg-orange-500/20" },
    approved: { label: "승인됨", color: "text-green-400 bg-green-500/20" },
    completed: { label: "완료", color: "text-blue-400 bg-blue-500/20" },
  };

  const statusInfo = statusConfig[prd.status] || statusConfig.draft;

  return (
    <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex items-start justify-between">
        <Link href={`/prd/${prd.id}`} className="flex-1 group">
          <h3 className="font-semibold group-hover:text-blue-400 transition-colors">
            {prd.title}
          </h3>
          <div className="flex items-center gap-3 mt-2 text-sm text-slate-400">
            <span>요구사항 {prd.requirements_count}개</span>
            {prd.created_at && (
              <>
                <span>·</span>
                <span>
                  {new Date(prd.created_at).toLocaleDateString("ko-KR")}
                </span>
              </>
            )}
          </div>
        </Link>

        <div className="flex items-center gap-2 ml-4">
          {/* Confidence Badge */}
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${confidenceColor}`}
          >
            {confidencePercent}%
          </span>

          {/* Status Badge */}
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${statusInfo.color}`}
          >
            {statusInfo.label}
          </span>

          {/* Export Button */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              title="내보내기"
            >
              <Download className="w-4 h-4 text-slate-400" />
            </button>

            {showExportMenu && (
              <div className="absolute right-0 top-full mt-1 bg-slate-700 rounded-lg shadow-lg border border-slate-600 z-10 min-w-[120px]">
                <button
                  onClick={() => {
                    onExport("markdown");
                    setShowExportMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-600 rounded-t-lg"
                >
                  Markdown
                </button>
                <button
                  onClick={() => {
                    onExport("json");
                    setShowExportMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-600"
                >
                  JSON
                </button>
                <button
                  onClick={() => {
                    onExport("html");
                    setShowExportMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-600 rounded-b-lg"
                >
                  HTML
                </button>
              </div>
            )}
          </div>

          {/* Delete Button */}
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="p-2 hover:bg-red-500/20 rounded-lg transition-colors disabled:opacity-50"
            title="삭제"
          >
            <Trash2 className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </div>
    </div>
  );
}
