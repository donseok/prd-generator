"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowLeft,
  Layers,
  Download,
  FileText,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Target,
  Shield,
  Lock,
  Flag,
} from "lucide-react";
import { api, type Requirement } from "@/lib/api";

export default function PRDViewerPage() {
  const params = useParams();
  const prdId = params.id as string;
  const [activeTab, setActiveTab] = useState<"overview" | "requirements" | "milestones" | "unresolved">("overview");
  const [expandedReqs, setExpandedReqs] = useState<Set<string>>(new Set());

  const { data: prd, isLoading, error } = useQuery({
    queryKey: ["prd", prdId],
    queryFn: () => api.getPRD(prdId),
  });

  const handleExport = async (format: "markdown" | "json" | "html") => {
    const data = await api.exportPRD(prdId, format);
    const blob = new Blob([typeof data === "string" ? data : JSON.stringify(data, null, 2)], {
      type: format === "json" ? "application/json" : "text/plain",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${prd?.title || "prd"}.${format === "markdown" ? "md" : format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleReq = (id: string) => {
    setExpandedReqs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !prd) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-red-400">PRD를 불러올 수 없습니다</p>
          <Link href="/" className="text-blue-400 hover:underline mt-4 inline-block">
            홈으로 돌아가기
          </Link>
        </div>
      </div>
    );
  }

  const allRequirements = [
    ...prd.functional_requirements,
    ...prd.non_functional_requirements,
    ...prd.constraints,
  ];
  const confidencePercent = Math.round(prd.metadata.overall_confidence * 100);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-xl font-bold">{prd.title}</h1>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-slate-400">v{prd.metadata.version}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    prd.metadata.status === "approved"
                      ? "bg-green-500/20 text-green-400"
                      : prd.metadata.status === "review"
                      ? "bg-yellow-500/20 text-yellow-400"
                      : "bg-slate-500/20 text-slate-400"
                  }`}>
                    {prd.metadata.status}
                  </span>
                  <ConfidenceBadge score={prd.metadata.overall_confidence} />
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleExport("markdown")}
                className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm"
              >
                <Download className="w-4 h-4" />
                MD
              </button>
              <button
                onClick={() => handleExport("json")}
                className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm"
              >
                <Download className="w-4 h-4" />
                JSON
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-slate-700">
          {[
            { key: "overview", label: "개요" },
            { key: "requirements", label: `요구사항 (${allRequirements.length})` },
            { key: "milestones", label: `마일스톤 (${prd.milestones.length})` },
            { key: "unresolved", label: `미해결 (${prd.unresolved_items.length})` },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as typeof activeTab)}
              className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.key
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="space-y-6 animate-fadeIn">
            <Section title="배경">
              <p className="text-slate-300 leading-relaxed">{prd.overview.background}</p>
            </Section>
            <Section title="목표">
              <ul className="space-y-2">
                {prd.overview.goals.map((goal, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Target className="w-4 h-4 text-blue-400 mt-1 flex-shrink-0" />
                    <span className="text-slate-300">{goal}</span>
                  </li>
                ))}
              </ul>
            </Section>
            <Section title="범위">
              <p className="text-slate-300 leading-relaxed">{prd.overview.scope}</p>
              {prd.overview.out_of_scope.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-slate-400 mb-2">범위 외:</h4>
                  <ul className="space-y-1">
                    {prd.overview.out_of_scope.map((item, i) => (
                      <li key={i} className="text-slate-400 text-sm">• {item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Section>
            {prd.overview.target_users.length > 0 && (
              <Section title="대상 사용자">
                <div className="flex flex-wrap gap-2">
                  {prd.overview.target_users.map((user, i) => (
                    <span key={i} className="px-3 py-1 bg-slate-700 rounded-full text-sm">
                      {user}
                    </span>
                  ))}
                </div>
              </Section>
            )}
            {prd.overview.success_metrics.length > 0 && (
              <Section title="성공 지표">
                <ul className="space-y-2">
                  {prd.overview.success_metrics.map((metric, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-400 mt-1 flex-shrink-0" />
                      <span className="text-slate-300">{metric}</span>
                    </li>
                  ))}
                </ul>
              </Section>
            )}
          </div>
        )}

        {activeTab === "requirements" && (
          <div className="space-y-4 animate-fadeIn">
            {/* FR */}
            {prd.functional_requirements.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-blue-400 mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  기능 요구사항 (FR)
                </h3>
                <div className="space-y-2">
                  {prd.functional_requirements.map((req) => (
                    <RequirementCard
                      key={req.id}
                      req={req}
                      expanded={expandedReqs.has(req.id)}
                      onToggle={() => toggleReq(req.id)}
                    />
                  ))}
                </div>
              </div>
            )}
            {/* NFR */}
            {prd.non_functional_requirements.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-medium text-purple-400 mb-3 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  비기능 요구사항 (NFR)
                </h3>
                <div className="space-y-2">
                  {prd.non_functional_requirements.map((req) => (
                    <RequirementCard
                      key={req.id}
                      req={req}
                      expanded={expandedReqs.has(req.id)}
                      onToggle={() => toggleReq(req.id)}
                    />
                  ))}
                </div>
              </div>
            )}
            {/* Constraints */}
            {prd.constraints.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-medium text-amber-400 mb-3 flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  제약조건
                </h3>
                <div className="space-y-2">
                  {prd.constraints.map((req) => (
                    <RequirementCard
                      key={req.id}
                      req={req}
                      expanded={expandedReqs.has(req.id)}
                      onToggle={() => toggleReq(req.id)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "milestones" && (
          <div className="space-y-4 animate-fadeIn">
            {prd.milestones.map((ms, i) => (
              <div
                key={ms.id}
                className="p-4 bg-slate-800/50 rounded-lg border border-slate-700"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">
                    {i + 1}
                  </div>
                  <h3 className="font-semibold">{ms.name}</h3>
                </div>
                <p className="text-slate-400 text-sm ml-11">{ms.description}</p>
                {ms.deliverables.length > 0 && (
                  <div className="mt-3 ml-11">
                    <h4 className="text-xs text-slate-500 mb-1">산출물:</h4>
                    <ul className="space-y-1">
                      {ms.deliverables.map((d, j) => (
                        <li key={j} className="text-sm text-slate-300">• {d}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === "unresolved" && (
          <div className="space-y-3 animate-fadeIn">
            {prd.unresolved_items.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
                <p>미해결 사항이 없습니다</p>
              </div>
            ) : (
              prd.unresolved_items.map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-slate-800/50 rounded-lg border border-slate-700"
                >
                  <div className="flex items-start gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs uppercase ${
                      item.type === "question" ? "bg-blue-500/20 text-blue-400" :
                      item.type === "decision" ? "bg-purple-500/20 text-purple-400" :
                      item.type === "risk" ? "bg-red-500/20 text-red-400" :
                      "bg-slate-500/20 text-slate-400"
                    }`}>
                      {item.type}
                    </span>
                    <div className="flex-1">
                      <p className="text-slate-200">{item.description}</p>
                      {item.suggested_action && (
                        <p className="text-sm text-slate-400 mt-1">
                          제안: {item.suggested_action}
                        </p>
                      )}
                    </div>
                    <span className={`text-xs ${
                      item.priority === "HIGH" ? "text-red-400" :
                      item.priority === "LOW" ? "text-slate-400" :
                      "text-yellow-400"
                    }`}>
                      {item.priority}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-6">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      {children}
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
  const confidencePercent = Math.round(req.confidence_score * 100);

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-4 text-left flex items-start gap-3 hover:bg-slate-700/30 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 mt-1 text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 mt-1 text-slate-400" />
        )}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-slate-500">{req.id}</span>
            <span className={`px-1.5 py-0.5 rounded text-xs ${
              req.priority === "HIGH" ? "bg-red-500/20 text-red-400" :
              req.priority === "LOW" ? "bg-slate-500/20 text-slate-400" :
              "bg-yellow-500/20 text-yellow-400"
            }`}>
              {req.priority}
            </span>
          </div>
          <h4 className="font-medium">{req.title}</h4>
        </div>
        <ConfidenceBadge score={req.confidence_score} />
      </button>

      {expanded && (
        <div className="px-4 pb-4 pl-11 space-y-4 animate-fadeIn">
          <div>
            <h5 className="text-xs text-slate-500 mb-1">설명</h5>
            <p className="text-sm text-slate-300">{req.description}</p>
          </div>
          {req.user_story && (
            <div>
              <h5 className="text-xs text-slate-500 mb-1">User Story</h5>
              <p className="text-sm text-slate-300 italic">{req.user_story}</p>
            </div>
          )}
          {req.acceptance_criteria.length > 0 && (
            <div>
              <h5 className="text-xs text-slate-500 mb-1">Acceptance Criteria</h5>
              <ul className="space-y-1">
                {req.acceptance_criteria.map((ac, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 mt-1 text-green-400 flex-shrink-0" />
                    {ac}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {req.assumptions.length > 0 && (
            <div>
              <h5 className="text-xs text-slate-500 mb-1">가정사항</h5>
              <ul className="space-y-1">
                {req.assumptions.map((a, i) => (
                  <li key={i} className="text-sm text-amber-400">• {a}</li>
                ))}
              </ul>
            </div>
          )}
          {req.missing_info.length > 0 && (
            <div>
              <h5 className="text-xs text-slate-500 mb-1">누락 정보</h5>
              <ul className="space-y-1">
                {req.missing_info.map((m, i) => (
                  <li key={i} className="text-sm text-red-400">• {m}</li>
                ))}
              </ul>
            </div>
          )}
          {req.confidence_reason && (
            <div>
              <h5 className="text-xs text-slate-500 mb-1">신뢰도 이유</h5>
              <p className="text-sm text-slate-400">{req.confidence_reason}</p>
            </div>
          )}
        </div>
      )}
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
