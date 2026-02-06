"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Layers,
  XCircle,
  Loader2,
  RefreshCw,
  FileText,
  Target,
  Sparkles,
  TrendingUp,
  FileCode,
  Presentation,
  Sun,
  Moon,
  Trash2,
} from "lucide-react";
import { api, OutputDocument, InputFile } from "@/lib/api";

// 문서 타입 필터
type DocTypeFilter = "all" | "PRD" | "TRD" | "WBS" | "Proposal" | "PPT";

// 문서 타입별 설정
const DOC_TYPE_CONFIG: Record<string, { label: string; gradient: string; icon: typeof FileText }> = {
  PRD: { label: "제품요구사항문서 (PRD)", gradient: "from-violet-400 to-purple-600", icon: FileText },
  TRD: { label: "기술요구사항문서 (TRD)", gradient: "from-blue-400 to-cyan-600", icon: FileCode },
  WBS: { label: "작업분해구조서 (WBS)", gradient: "from-emerald-400 to-teal-600", icon: Target },
  Proposal: { label: "제안서", gradient: "from-amber-400 to-orange-600", icon: FileText },
  PPT: { label: "PPT", gradient: "from-rose-400 to-pink-600", icon: Presentation },
};

export default function MainPage() {
  const [docFilter, setDocFilter] = useState<DocTypeFilter>("all");
  const [mounted, setMounted] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [inputFiles, setInputFiles] = useState<InputFile[]>([]);
  const [loadingInputs, setLoadingInputs] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
      setIsDarkMode(false);
    }
  }, []);

  const toggleTheme = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem("theme", newMode ? "dark" : "light");
  };

  const fetchInputFiles = async () => {
    setLoadingInputs(true);
    try {
      const response = await api.listInputFiles();
      setInputFiles(response.files);
    } catch (error) {
      console.error("입력 파일 조회 실패:", error);
    } finally {
      setLoadingInputs(false);
    }
  };

  const handleGenerate = async () => {
    if (inputFiles.length === 0) {
      alert("입력 파일이 없습니다. workspace/inputs/projects/ 폴더에 요구사항 파일을 배치해주세요.");
      return;
    }
    setGenerating(true);
    try {
      const response = await api.generateDocuments(["prd"]);
      alert(`문서 생성이 시작되었습니다.\n작업 ID: ${response.job_id}\n${response.message}`);
      setShowGenerateModal(false);
      refetchOutputs();
    } catch (error) {
      console.error("문서 생성 실패:", error);
      alert("문서 생성 시작에 실패했습니다.");
    } finally {
      setGenerating(false);
    }
  };

  const openGenerateModal = () => {
    setShowGenerateModal(true);
    fetchInputFiles();
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

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-[#0a0a0f] text-white' : 'bg-gradient-to-br from-slate-50 to-blue-50 text-slate-900'} overflow-hidden transition-colors duration-500`}>
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br ${isDarkMode ? 'from-violet-600/20' : 'from-violet-300/30'} via-transparent to-transparent rounded-full blur-3xl animate-pulse`} />
        <div className={`absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl ${isDarkMode ? 'from-cyan-600/20' : 'from-cyan-300/30'} via-transparent to-transparent rounded-full blur-3xl animate-pulse`} style={{ animationDelay: "1s" }} />
        <div className={`absolute top-1/4 right-1/4 w-96 h-96 bg-gradient-to-br ${isDarkMode ? 'from-fuchsia-600/10' : 'from-fuchsia-300/20'} to-transparent rounded-full blur-3xl animate-pulse`} style={{ animationDelay: "2s" }} />
      </div>

      {/* Grid Pattern Overlay */}
      <div
        className="fixed inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}
      />

      {/* 헤더 */}
      <header className={`relative border-b ${isDarkMode ? 'border-white/10 bg-black/40' : 'border-slate-200 bg-white/70'} backdrop-blur-xl sticky top-0 z-50`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-2xl blur-lg opacity-60" />
                <div className="relative p-3 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-2xl text-white font-extrabold text-lg leading-none flex items-center justify-center">
                  DK
                </div>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-white via-white to-white/60 bg-clip-text text-transparent">
                  문서 자동 생성시스템
                </h1>
                <div className="flex items-center gap-2 text-xs text-white/40">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  {mounted ? new Date(outputsUpdatedAt).toLocaleTimeString("ko-KR") : "로딩 중..."} 업데이트
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={toggleTheme}
                className={`p-2.5 ${isDarkMode ? 'bg-white/5 hover:bg-white/10 border-white/10 hover:border-white/20' : 'bg-slate-100 hover:bg-slate-200 border-slate-200 hover:border-slate-300'} border rounded-xl transition-all duration-300 hover:scale-105`}
                title={isDarkMode ? "라이트 모드" : "다크 모드"}
              >
                {isDarkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
              </button>
              <button
                onClick={() => refetchOutputs()}
                className={`flex items-center gap-2 px-4 py-2.5 ${isDarkMode ? 'bg-white/5 hover:bg-white/10 border-white/10 hover:border-white/20' : 'bg-slate-100 hover:bg-slate-200 border-slate-200 hover:border-slate-300'} border rounded-xl transition-all duration-300 hover:scale-105`}
              >
                <RefreshCw className="w-4 h-4" />
                <span className="hidden sm:inline">새로고침</span>
              </button>
              <button
                onClick={handleDeleteAll}
                disabled={deleting || outputs.length === 0}
                className={`group flex items-center gap-2 px-4 py-2.5 ${isDarkMode ? 'bg-red-500/10 hover:bg-red-500/20 border-red-500/30 hover:border-red-500/50' : 'bg-red-50 hover:bg-red-100 border-red-200 hover:border-red-300'} border rounded-xl transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed`}
                title="생성된 문서 모두 삭제"
              >
                {deleting ? (
                  <Loader2 className="w-4 h-4 animate-spin text-red-500" />
                ) : (
                  <Trash2 className="w-4 h-4 text-red-500" />
                )}
                <span className={`hidden sm:inline font-medium ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>문서 삭제</span>
              </button>
              <button
                onClick={openGenerateModal}
                className="group flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-violet-500/25"
              >
                <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                <span className="font-medium">새 문서 생성</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative max-w-7xl mx-auto px-6 py-8">
        {/* 문서 타입별 통계 카드 */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
          <GlassStatCard
            icon={<TrendingUp />}
            label="전체"
            value={docStats.total}
            gradient="from-violet-500 to-purple-600"
            delay={0}
          />
          <GlassStatCard
            icon={<FileText />}
            label="PRD"
            value={docStats.PRD}
            gradient="from-violet-400 to-purple-600"
            delay={0.1}
          />
          <GlassStatCard
            icon={<FileCode />}
            label="TRD"
            value={docStats.TRD}
            gradient="from-blue-400 to-cyan-600"
            delay={0.2}
          />
          <GlassStatCard
            icon={<Target />}
            label="WBS"
            value={docStats.WBS}
            gradient="from-emerald-400 to-teal-600"
            delay={0.3}
          />
          <GlassStatCard
            icon={<FileText />}
            label="제안서"
            value={docStats.Proposal}
            gradient="from-amber-400 to-orange-600"
            delay={0.4}
          />
          <GlassStatCard
            icon={<Presentation />}
            label="PPT"
            value={docStats.PPT}
            gradient="from-rose-400 to-pink-600"
            delay={0.5}
          />
        </div>

        {/* 문서 타입 필터 */}
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2 scrollbar-hide">
          {(["all", "PRD", "TRD", "WBS", "Proposal", "PPT"] as const).map((type) => {
            const config = type === "all" ? null : DOC_TYPE_CONFIG[type];
            const Icon = config?.icon || Layers;
            const count = type === "all" ? docStats.total : docStats[type];
            return (
              <button
                key={type}
                onClick={() => setDocFilter(type)}
                className={`group flex items-center gap-2 px-5 py-3 rounded-xl font-medium transition-all duration-300 whitespace-nowrap ${docFilter === type
                  ? "bg-gradient-to-r from-violet-600/90 to-cyan-600/90 text-white shadow-lg shadow-violet-500/20"
                  : isDarkMode
                    ? "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/5 hover:border-white/10"
                    : "bg-white/70 text-slate-600 hover:bg-white hover:text-slate-900 border border-slate-200 hover:border-slate-300 shadow-sm"
                  }`}
              >
                <Icon className="w-4 h-4" />
                {type === "all" ? "전체" : config?.label || type}
                <span className={`px-2 py-0.5 rounded-full text-xs ${docFilter === type ? "bg-white/20" : "bg-white/10"
                  }`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* 문서 목록 */}
        {outputsLoading ? (
          <LoadingSpinner />
        ) : filteredOutputs.length === 0 ? (
          <EmptyState
            message={docFilter === "all" ? "아직 생성된 문서가 없습니다" : `${docFilter} 타입의 문서가 없습니다`}
            subMessage="CLI에서 문서를 생성해보세요"
            onAction={openGenerateModal}
          />
        ) : (
          <div className="grid gap-4">
            {filteredOutputs.map((doc, index) => (
              <DocumentCard key={doc.id} doc={doc} index={index} />
            ))}
          </div>
        )}

        {/* 문서 생성 모달 */}
        {showGenerateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="relative w-full max-w-lg mx-4 p-6 bg-[#0f0f15] border border-white/10 rounded-3xl shadow-2xl">
              <button
                onClick={() => setShowGenerateModal(false)}
                className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <XCircle className="w-5 h-5" />
              </button>

              <h2 className="text-xl font-bold mb-2">새 문서 생성</h2>
              <p className="text-white/50 text-sm mb-6">
                workspace/inputs/projects/ 폴더의 파일로 PRD를 생성합니다.
              </p>

              <div className="mb-6">
                <h3 className="text-sm font-medium text-white/60 mb-3">입력 파일</h3>
                <div className="max-h-48 overflow-y-auto space-y-2 p-4 bg-white/5 rounded-xl border border-white/10">
                  {loadingInputs ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="w-5 h-5 animate-spin text-white/40" />
                    </div>
                  ) : inputFiles.length === 0 ? (
                    <p className="text-white/40 text-sm text-center py-4">
                      입력 파일이 없습니다.
                      <br />
                      <span className="text-xs">workspace/inputs/projects/ 폴더에 파일을 배치해주세요.</span>
                    </p>
                  ) : (
                    inputFiles.map((file) => (
                      <div
                        key={file.name}
                        className="flex items-center gap-3 px-3 py-2 bg-white/5 rounded-lg"
                      >
                        <FileText className="w-4 h-4 text-violet-400" />
                        <span className="flex-1 truncate text-sm">{file.name}</span>
                        <span className="text-xs text-white/40">
                          {(file.size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowGenerateModal(false)}
                  className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={generating || inputFiles.length === 0}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      생성 중...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      PRD 생성 시작
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// 문서 카드 컴포넌트
function DocumentCard({ doc, index }: { doc: OutputDocument; index: number }) {
  const config = DOC_TYPE_CONFIG[doc.doc_type] || DOC_TYPE_CONFIG.PRD;
  const Icon = config.icon;

  return (
    <div
      className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl transition-all duration-500 hover:border-white/20 hover:bg-white/10 hover:scale-[1.01] hover:shadow-2xl hover:shadow-violet-500/10"
      style={{
        animationDelay: `${index * 0.05}s`,
        animation: 'fadeInUp 0.5s ease-out forwards',
        opacity: 0
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-r from-violet-600/0 via-violet-600/5 to-cyan-600/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-4 mb-3">
              <div className={`relative p-3 rounded-xl bg-gradient-to-br ${config.gradient} shadow-lg`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-lg truncate group-hover:text-white transition-colors">
                  {doc.title}
                </h3>
                <p className="text-sm text-white/40">
                  {new Date(doc.created_at).toLocaleString("ko-KR")}
                </p>
              </div>
            </div>

            {/* 파일 타입 태그 */}
            <div className="flex flex-wrap gap-2 mt-4">
              {doc.has_json && (
                <span className="px-3 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-lg text-xs text-blue-400">
                  JSON
                </span>
              )}
              {doc.has_md && (
                <span className="px-3 py-1.5 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-xs text-emerald-400">
                  Markdown
                </span>
              )}
              {doc.has_pptx && (
                <span className="px-3 py-1.5 bg-rose-500/20 border border-rose-500/30 rounded-lg text-xs text-rose-400">
                  PPTX
                </span>
              )}
            </div>
          </div>

          {/* 문서 타입 뱃지 */}
          <div className="flex flex-col items-end gap-2">
            <span className={`px-4 py-2 rounded-xl text-sm font-medium bg-gradient-to-r ${config.gradient} shadow-lg`}>
              {config.label}
            </span>
            <span className="px-4 py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-green-400 to-emerald-500 shadow-lg">
              완료
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// 로딩 스피너 컴포넌트
function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full blur-xl opacity-40 animate-pulse" />
        <Loader2 className="relative w-16 h-16 animate-spin text-white" />
      </div>
      <p className="mt-6 text-white/40 font-medium">데이터를 불러오는 중...</p>
    </div>
  );
}

// 빈 상태 컴포넌트
function EmptyState({ message, subMessage, onAction }: { message: string; subMessage: string; onAction?: () => void }) {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl">
      <div className="absolute inset-0 bg-gradient-to-br from-violet-600/5 via-transparent to-cyan-600/5" />
      <div className="relative flex flex-col items-center justify-center py-20 px-6">
        <div className="relative mb-6">
          <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 to-cyan-500/20 rounded-3xl blur-2xl" />
          <div className="relative p-6 bg-white/5 rounded-3xl border border-white/10">
            <FileText className="w-12 h-12 text-white/40" />
          </div>
        </div>
        <p className="text-xl font-medium text-white/60 mb-2">{message}</p>
        <p className="text-white/30 mb-8">{subMessage}</p>
        {onAction && (
          <button
            onClick={onAction}
            className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-violet-500/25"
          >
            <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            <span className="font-medium">첫 PRD 만들기</span>
          </button>
        )}
      </div>
    </div>
  );
}

// 글래스모피즘 통계 카드 컴포넌트
function GlassStatCard({
  icon,
  label,
  value,
  gradient,
  delay,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  gradient: string;
  delay: number;
}) {
  return (
    <div
      className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-5 transition-all duration-500 hover:border-white/20 hover:bg-white/10 hover:scale-105 hover:shadow-xl"
      style={{
        animationDelay: `${delay}s`,
        animation: 'fadeInUp 0.5s ease-out forwards',
        opacity: 0
      }}
    >
      <div className={`absolute -top-10 -right-10 w-24 h-24 bg-gradient-to-br ${gradient} rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity duration-500`} />

      <div className="relative flex items-center gap-4">
        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
          {icon}
        </div>
        <div>
          <div className="text-3xl font-bold text-white">{value}</div>
          <div className="text-sm text-white/40 font-medium">{label}</div>
        </div>
      </div>
    </div>
  );
}
