"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Layers,
  X,
  Loader2,
  RefreshCw,
  FileText,
  Target,
  TrendingUp,
  FileCode,
  Presentation,
  Sun,
  Moon,
  Trash2,
  Clock,
  FolderOpen,
  CheckCircle2,
  Code2,
  FileType,
} from "lucide-react";
import { api, OutputDocument } from "@/lib/api";

// 콘텐츠 뷰어 상태 타입
interface ContentViewerState {
  isOpen: boolean;
  docId: string;
  docTitle: string;
  format: "json" | "md";
  content: string;
  loading: boolean;
}

// 문서 타입 필터
type DocTypeFilter = "all" | "PRD" | "TRD" | "WBS" | "Proposal" | "PPT";

// 문서 타입별 설정
const DOC_TYPE_CONFIG: Record<string, {
  label: string;
  shortLabel: string;
  gradient: string;
  bgColor: string;
  icon: typeof FileText
}> = {
  PRD: {
    label: "제품요구사항문서",
    shortLabel: "PRD",
    gradient: "from-violet-500 to-purple-600",
    bgColor: "bg-violet-500/10",
    icon: FileText
  },
  TRD: {
    label: "기술요구사항문서",
    shortLabel: "TRD",
    gradient: "from-blue-500 to-cyan-500",
    bgColor: "bg-blue-500/10",
    icon: FileCode
  },
  WBS: {
    label: "작업분해구조서",
    shortLabel: "WBS",
    gradient: "from-emerald-500 to-teal-500",
    bgColor: "bg-emerald-500/10",
    icon: Target
  },
  Proposal: {
    label: "제안서",
    shortLabel: "제안서",
    gradient: "from-amber-500 to-orange-500",
    bgColor: "bg-amber-500/10",
    icon: FileText
  },
  PPT: {
    label: "프레젠테이션",
    shortLabel: "PPT",
    gradient: "from-rose-500 to-pink-500",
    bgColor: "bg-rose-500/10",
    icon: Presentation
  },
};

export default function MainPage() {
  const [docFilter, setDocFilter] = useState<DocTypeFilter>("all");
  const [mounted, setMounted] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [contentViewer, setContentViewer] = useState<ContentViewerState>({
    isOpen: false,
    docId: "",
    docTitle: "",
    format: "json",
    content: "",
    loading: false,
  });

  // CLI 생성 문서 목록 조회
  const { data: outputsData, isLoading: outputsLoading, refetch: refetchOutputs, dataUpdatedAt: outputsUpdatedAt } = useQuery({
    queryKey: ["output-documents"],
    queryFn: () => api.listOutputDocuments(),
    refetchInterval: 30000,
  });

  const outputs = outputsData?.documents || [];

  const filteredOutputs = outputs.filter((doc) => {
    if (docFilter === "all") return true;
    return doc.doc_type === docFilter;
  });

  const docStats = {
    total: outputs.length,
    PRD: outputs.filter((d) => d.doc_type === "PRD").length,
    TRD: outputs.filter((d) => d.doc_type === "TRD").length,
    WBS: outputs.filter((d) => d.doc_type === "WBS").length,
    Proposal: outputs.filter((d) => d.doc_type === "Proposal").length,
    PPT: outputs.filter((d) => d.doc_type === "PPT").length,
  };

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      setIsDarkMode(true);
    }
  }, []);

  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem("theme", newMode ? "dark" : "light");
  };

  const openContentViewer = async (doc: OutputDocument, format: "json" | "md") => {
    setContentViewer({
      isOpen: true,
      docId: doc.id,
      docTitle: doc.title,
      format,
      content: "",
      loading: true,
    });

    try {
      const response = await api.getOutputDocument(doc.id, format);
      let content = "";
      if (format === "json" && response.content_json) {
        content = JSON.stringify(response.content_json, null, 2);
      } else if (format === "md" && response.content_md) {
        content = response.content_md;
      }
      setContentViewer((prev) => ({ ...prev, content, loading: false }));
    } catch (error) {
      console.error("문서 내용 로드 실패:", error);
      setContentViewer((prev) => ({
        ...prev,
        content: "문서 내용을 불러오는 데 실패했습니다.",
        loading: false,
      }));
    }
  };

  const closeContentViewer = () => {
    setContentViewer({
      isOpen: false,
      docId: "",
      docTitle: "",
      format: "json",
      content: "",
      loading: false,
    });
  };

  const handleDeleteAll = async () => {
    if (outputs.length === 0) {
      alert("삭제할 문서가 없습니다.");
      return;
    }

    const confirmed = confirm(
      `정말로 ${outputs.length}개의 생성된 문서를 모두 삭제하시겠습니까?\n\n삭제된 파일은 복구할 수 없습니다.`
    );

    if (!confirmed) return;

    setDeleting(true);
    try {
      const response = await api.deleteAllDocuments();
      alert(`${response.message}\n\n상세:\n- PRD: ${response.details.prd || 0}개\n- TRD: ${response.details.trd || 0}개\n- WBS: ${response.details.wbs || 0}개\n- 제안서: ${response.details.proposals || 0}개\n- PPT: ${response.details.ppt || 0}개`);
      refetchOutputs();
    } catch (error) {
      console.error("문서 삭제 실패:", error);
      alert("문서 삭제에 실패했습니다.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-500 ${isDarkMode ? 'bg-[#08080c]' : 'bg-slate-50'}`}>
      {/* Ambient Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Orbs */}
        <div
          className="absolute -top-[40%] -left-[20%] w-[70%] h-[70%] rounded-full opacity-30 blur-[120px] animate-pulse-glow"
          style={{ background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, transparent 70%)' }}
        />
        <div
          className="absolute -bottom-[30%] -right-[20%] w-[60%] h-[60%] rounded-full opacity-25 blur-[100px] animate-pulse-glow"
          style={{ background: 'radial-gradient(circle, rgba(6, 182, 212, 0.4) 0%, transparent 70%)', animationDelay: '1.5s' }}
        />
        <div
          className="absolute top-[20%] right-[10%] w-[30%] h-[30%] rounded-full opacity-20 blur-[80px] animate-float"
          style={{ background: 'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%)' }}
        />

        {/* Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      {/* Header */}
      <header className={`relative z-50 ${isDarkMode ? 'bg-[#08080c]/80' : 'bg-white/80'} backdrop-blur-xl border-b ${isDarkMode ? 'border-white/[0.06]' : 'border-slate-200'}`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo & Title */}
            <div className="flex items-center gap-4">
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-2xl blur-xl opacity-60 group-hover:opacity-80 transition-opacity" />
                <div className="relative w-12 h-12 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-2xl flex items-center justify-center text-white font-black text-lg shadow-lg">
                  DK
                </div>
              </div>
              <div>
                <h1 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                  문서 자동 생성시스템
                </h1>
                <div className={`flex items-center gap-2 text-xs ${isDarkMode ? 'text-white/40' : 'text-slate-500'}`}>
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                  </span>
                  <Clock className="w-3 h-3" />
                  {mounted && outputsUpdatedAt ? new Date(outputsUpdatedAt).toLocaleTimeString("ko-KR") : "로딩 중..."}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={toggleTheme}
                className={`p-2.5 rounded-xl transition-all duration-300 hover:scale-105 ${isDarkMode
                  ? 'bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06]'
                  : 'bg-slate-100 hover:bg-slate-200 border border-slate-200'
                  }`}
                title={isDarkMode ? "라이트 모드" : "다크 모드"}
              >
                {isDarkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
              </button>

              <button
                onClick={() => refetchOutputs()}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all duration-300 hover:scale-105 ${isDarkMode
                  ? 'bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] text-white/80'
                  : 'bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700'
                  }`}
              >
                <RefreshCw className="w-4 h-4" />
                <span className="hidden sm:inline text-sm font-medium">새로고침</span>
              </button>

              <button
                onClick={handleDeleteAll}
                disabled={deleting || outputs.length === 0}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all duration-300 hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 ${isDarkMode
                  ? 'bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400'
                  : 'bg-red-50 hover:bg-red-100 border border-red-200 text-red-600'
                  }`}
              >
                {deleting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                <span className="hidden sm:inline text-sm font-medium">삭제</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid - Bento Style */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
          <StatCard
            icon={<TrendingUp className="w-5 h-5" />}
            label="전체"
            value={docStats.total}
            gradient="from-violet-500 to-cyan-500"
            delay={0}
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<FileText className="w-5 h-5" />}
            label="PRD"
            value={docStats.PRD}
            gradient="from-violet-500 to-purple-600"
            delay={1}
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<FileCode className="w-5 h-5" />}
            label="TRD"
            value={docStats.TRD}
            gradient="from-blue-500 to-cyan-500"
            delay={2}
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<Target className="w-5 h-5" />}
            label="WBS"
            value={docStats.WBS}
            gradient="from-emerald-500 to-teal-500"
            delay={3}
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<FileText className="w-5 h-5" />}
            label="제안서"
            value={docStats.Proposal}
            gradient="from-amber-500 to-orange-500"
            delay={4}
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<Presentation className="w-5 h-5" />}
            label="PPT"
            value={docStats.PPT}
            gradient="from-rose-500 to-pink-500"
            delay={5}
            isDarkMode={isDarkMode}
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
          {(["all", "PRD", "TRD", "WBS", "Proposal", "PPT"] as const).map((type) => {
            const config = type === "all" ? null : DOC_TYPE_CONFIG[type];
            const Icon = config?.icon || Layers;
            const count = type === "all" ? docStats.total : docStats[type];
            const isActive = docFilter === type;

            return (
              <button
                key={type}
                onClick={() => setDocFilter(type)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all duration-300 whitespace-nowrap text-sm ${isActive
                  ? "bg-gradient-to-r from-violet-500/90 to-cyan-500/90 text-white shadow-lg shadow-violet-500/20"
                  : isDarkMode
                    ? "bg-white/[0.02] text-white/50 hover:bg-white/[0.05] hover:text-white/80 border border-white/[0.04]"
                    : "bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200"
                  }`}
              >
                <Icon className="w-4 h-4" />
                <span>{type === "all" ? "전체" : config?.shortLabel || type}</span>
                <span className={`px-1.5 py-0.5 rounded-md text-xs ${isActive ? "bg-white/20" : isDarkMode ? "bg-white/10" : "bg-slate-100"}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Document List */}
        {outputsLoading ? (
          <LoadingState isDarkMode={isDarkMode} />
        ) : filteredOutputs.length === 0 ? (
          <EmptyState
            message={docFilter === "all" ? "아직 생성된 문서가 없습니다" : `${docFilter} 타입의 문서가 없습니다`}
            subMessage="에이전트(@auto-doc)를 사용해 문서를 생성해보세요"
            isDarkMode={isDarkMode}
          />
        ) : (
          <div className="space-y-3">
            {filteredOutputs.map((doc, index) => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                index={index}
                onViewContent={openContentViewer}
                isDarkMode={isDarkMode}
              />
            ))}
          </div>
        )}

        {/* Content Viewer Modal */}
        {contentViewer.isOpen && (
          <ContentViewerModal
            contentViewer={contentViewer}
            onClose={closeContentViewer}
            isDarkMode={isDarkMode}
          />
        )}
      </main>
    </div>
  );
}

// Stat Card Component
function StatCard({
  icon,
  label,
  value,
  gradient,
  delay,
  isDarkMode,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  gradient: string;
  delay: number;
  isDarkMode: boolean;
}) {
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl p-4 transition-all duration-300 hover:scale-[1.02] ${isDarkMode
        ? 'bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1]'
        : 'bg-white border border-slate-200 hover:border-slate-300 hover:shadow-lg'
        }`}
      style={{
        animation: `fadeInUp 0.5s ease-out forwards`,
        animationDelay: `${delay * 0.08}s`,
        opacity: 0
      }}
    >
      {/* Glow Effect */}
      <div className={`absolute -top-8 -right-8 w-20 h-20 bg-gradient-to-br ${gradient} rounded-full blur-2xl opacity-0 group-hover:opacity-30 transition-opacity duration-500`} />

      <div className="relative flex items-center gap-3">
        <div className={`p-2.5 rounded-xl bg-gradient-to-br ${gradient} text-white shadow-lg`}>
          {icon}
        </div>
        <div>
          <div className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
            {value}
          </div>
          <div className={`text-xs font-medium ${isDarkMode ? 'text-white/40' : 'text-slate-500'}`}>
            {label}
          </div>
        </div>
      </div>
    </div>
  );
}

// Document Card Component
function DocumentCard({
  doc,
  index,
  onViewContent,
  isDarkMode
}: {
  doc: OutputDocument;
  index: number;
  onViewContent: (doc: OutputDocument, format: "json" | "md") => void;
  isDarkMode: boolean;
}) {
  const config = DOC_TYPE_CONFIG[doc.doc_type] || DOC_TYPE_CONFIG.PRD;
  const Icon = config.icon;

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl transition-all duration-300 hover:scale-[1.005] ${isDarkMode
        ? 'bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1]'
        : 'bg-white border border-slate-200 hover:border-slate-300 hover:shadow-xl'
        }`}
      style={{
        animation: `fadeInUp 0.4s ease-out forwards`,
        animationDelay: `${index * 0.05}s`,
        opacity: 0
      }}
    >
      {/* Hover Glow */}
      <div className={`absolute inset-0 bg-gradient-to-r ${config.gradient} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-500`} />

      <div className="relative p-5">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Icon & Info */}
          <div className="flex items-center gap-4 min-w-0 flex-1">
            <div className={`shrink-0 p-3 rounded-xl bg-gradient-to-br ${config.gradient} text-white shadow-lg shadow-violet-500/10`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className={`font-semibold truncate mb-1 ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
                {doc.title}
              </h3>
              <div className={`flex items-center gap-3 text-xs ${isDarkMode ? 'text-white/40' : 'text-slate-500'}`}>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(doc.created_at).toLocaleString("ko-KR")}
                </span>
              </div>
            </div>
          </div>

          {/* Right: Badges & Actions */}
          <div className="flex items-center gap-3 shrink-0">
            {/* File Type Buttons */}
            <div className="flex gap-2">
              {doc.has_json && (
                <button
                  onClick={() => onViewContent(doc, "json")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${isDarkMode
                    ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 hover:border-blue-500/40'
                    : 'bg-blue-50 text-blue-600 border border-blue-200 hover:bg-blue-100'
                    }`}
                >
                  <Code2 className="w-3 h-3" />
                  JSON
                </button>
              )}
              {doc.has_md && (
                <button
                  onClick={() => onViewContent(doc, "md")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${isDarkMode
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 hover:border-emerald-500/40'
                    : 'bg-emerald-50 text-emerald-600 border border-emerald-200 hover:bg-emerald-100'
                    }`}
                >
                  <FileType className="w-3 h-3" />
                  MD
                </button>
              )}
              {doc.has_pptx && (
                <button
                  onClick={async () => {
                    try {
                      await api.openPptxFile(doc.id);
                    } catch (error) {
                      console.error("PPTX 파일 열기 실패:", error);
                      alert("PPTX 파일을 열 수 없습니다.");
                    }
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${isDarkMode
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 hover:border-rose-500/40'
                    : 'bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100'
                    }`}
                >
                  <Presentation className="w-3 h-3" />
                  PPTX
                </button>
              )}
            </div>

            {/* Status & Type Badges */}
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r ${config.gradient} text-white shadow-sm`}>
                {config.shortLabel}
              </span>
              <span className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/90 text-white shadow-sm">
                <CheckCircle2 className="w-3 h-3" />
                완료
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Loading State Component
function LoadingState({ isDarkMode }: { isDarkMode: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full blur-2xl opacity-40 animate-pulse" />
        <Loader2 className={`relative w-12 h-12 animate-spin ${isDarkMode ? 'text-white' : 'text-slate-700'}`} />
      </div>
      <p className={`mt-6 text-sm font-medium ${isDarkMode ? 'text-white/40' : 'text-slate-500'}`}>
        문서를 불러오는 중...
      </p>
    </div>
  );
}

// Empty State Component
function EmptyState({ message, subMessage, isDarkMode }: { message: string; subMessage: string; isDarkMode: boolean }) {
  return (
    <div className={`relative overflow-hidden rounded-3xl ${isDarkMode ? 'bg-white/[0.02] border border-white/[0.06]' : 'bg-white border border-slate-200'}`}>
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-violet-500/[0.03] via-transparent to-cyan-500/[0.03]" />

      <div className="relative flex flex-col items-center justify-center py-20 px-6">
        <div className="relative mb-6">
          <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 to-cyan-500/20 rounded-3xl blur-2xl animate-pulse" />
          <div className={`relative p-6 rounded-3xl ${isDarkMode ? 'bg-white/[0.03] border border-white/[0.06]' : 'bg-slate-50 border border-slate-200'}`}>
            <FolderOpen className={`w-12 h-12 ${isDarkMode ? 'text-white/30' : 'text-slate-400'}`} />
          </div>
        </div>
        <p className={`text-lg font-medium mb-2 ${isDarkMode ? 'text-white/60' : 'text-slate-600'}`}>{message}</p>
        <p className={`text-sm ${isDarkMode ? 'text-white/30' : 'text-slate-400'}`}>{subMessage}</p>
      </div>
    </div>
  );
}

// Content Viewer Modal Component
function ContentViewerModal({
  contentViewer,
  onClose,
  isDarkMode
}: {
  contentViewer: ContentViewerState;
  onClose: () => void;
  isDarkMode: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className={`relative w-full max-w-5xl max-h-[90vh] flex flex-col rounded-3xl shadow-2xl overflow-hidden ${isDarkMode ? 'bg-[#0d0d12] border border-white/[0.08]' : 'bg-white border border-slate-200'
        }`}>
        {/* Header */}
        <div className={`flex items-center justify-between p-5 border-b ${isDarkMode ? 'border-white/[0.06]' : 'border-slate-200'}`}>
          <div className="flex items-center gap-3">
            <h2 className={`text-lg font-bold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
              {contentViewer.docTitle}
            </h2>
            <span className={`px-3 py-1 rounded-lg text-xs font-medium ${contentViewer.format === "json"
              ? isDarkMode ? "bg-blue-500/15 text-blue-400 border border-blue-500/30" : "bg-blue-50 text-blue-600 border border-blue-200"
              : isDarkMode ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : "bg-emerald-50 text-emerald-600 border border-emerald-200"
              }`}>
              {contentViewer.format.toUpperCase()}
            </span>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition-colors ${isDarkMode ? 'hover:bg-white/10 text-white/60' : 'hover:bg-slate-100 text-slate-500'}`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {contentViewer.loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className={`w-8 h-8 animate-spin ${isDarkMode ? 'text-white/40' : 'text-slate-400'}`} />
            </div>
          ) : contentViewer.format === "md" ? (
            <div className={`prose prose-lg max-w-none ${isDarkMode ? 'prose-invert' : ''}`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {contentViewer.content}
              </ReactMarkdown>
            </div>
          ) : (
            <div className={`rounded-xl p-4 overflow-x-auto ${isDarkMode ? 'bg-[#08080c] border border-white/[0.06]' : 'bg-slate-50 border border-slate-200'}`}>
              <JsonViewer data={JSON.parse(contentViewer.content)} isDarkMode={isDarkMode} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// JSON Viewer Component
function JsonViewer({ data, isDarkMode, depth = 0 }: { data: unknown; isDarkMode: boolean; depth?: number }) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const toggleCollapse = (key: string) => {
    setCollapsed(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const renderValue = (value: unknown, key: string, currentDepth: number): React.ReactNode => {
    const textColor = isDarkMode ? {
      null: 'text-slate-500',
      boolean: 'text-amber-400',
      number: 'text-cyan-400',
      string: 'text-emerald-400',
      key: 'text-blue-400',
      bracket: 'text-slate-500'
    } : {
      null: 'text-slate-400',
      boolean: 'text-amber-600',
      number: 'text-cyan-600',
      string: 'text-emerald-600',
      key: 'text-blue-600',
      bracket: 'text-slate-400'
    };

    if (value === null) {
      return <span className={textColor.null}>null</span>;
    }
    if (typeof value === "boolean") {
      return <span className={textColor.boolean}>{value.toString()}</span>;
    }
    if (typeof value === "number") {
      return <span className={textColor.number}>{value}</span>;
    }
    if (typeof value === "string") {
      return <span className={textColor.string}>&quot;{value}&quot;</span>;
    }
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className={textColor.bracket}>[]</span>;
      }
      const isCollapsed = collapsed[key];
      return (
        <div className="inline">
          <button onClick={() => toggleCollapse(key)} className={`${textColor.bracket} hover:text-white mr-1`}>
            {isCollapsed ? "▶" : "▼"}
          </button>
          <span className={textColor.bracket}>[</span>
          <span className="text-violet-400 text-xs ml-1">{value.length} items</span>
          {!isCollapsed && (
            <div className={`ml-4 border-l ${isDarkMode ? 'border-white/10' : 'border-slate-200'} pl-3`}>
              {value.map((item, idx) => (
                <div key={idx} className="my-1">
                  {renderValue(item, `${key}-${idx}`, currentDepth + 1)}
                  {idx < value.length - 1 && <span className={textColor.bracket}>,</span>}
                </div>
              ))}
            </div>
          )}
          <span className={textColor.bracket}>]</span>
        </div>
      );
    }
    if (typeof value === "object") {
      const entries = Object.entries(value as Record<string, unknown>);
      if (entries.length === 0) {
        return <span className={textColor.bracket}>{"{}"}</span>;
      }
      const isCollapsed = collapsed[key];
      return (
        <div className="inline">
          <button onClick={() => toggleCollapse(key)} className={`${textColor.bracket} hover:text-white mr-1`}>
            {isCollapsed ? "▶" : "▼"}
          </button>
          <span className={textColor.bracket}>{"{"}</span>
          <span className="text-violet-400 text-xs ml-1">{entries.length} keys</span>
          {!isCollapsed && (
            <div className={`ml-4 border-l ${isDarkMode ? 'border-white/10' : 'border-slate-200'} pl-3`}>
              {entries.map(([k, v], idx) => (
                <div key={k} className="my-1">
                  <span className={textColor.key}>&quot;{k}&quot;</span>
                  <span className={textColor.bracket}>: </span>
                  {renderValue(v, `${key}-${k}`, currentDepth + 1)}
                  {idx < entries.length - 1 && <span className={textColor.bracket}>,</span>}
                </div>
              ))}
            </div>
          )}
          <span className={textColor.bracket}>{"}"}</span>
        </div>
      );
    }
    return <span className={textColor.null}>{String(value)}</span>;
  };

  return (
    <div className="font-mono text-sm leading-relaxed">
      {renderValue(data, "root", depth)}
    </div>
  );
}
