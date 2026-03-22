"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  AlertCircle,
  ArrowRightLeft,
  Box,
  ChevronDown,
  ChevronRight,
  Code2,
  Database,
  Download,
  Layers,
  Loader2,
  Server,
} from "lucide-react";
import { api } from "@/lib/api";
import { AppShell, MetricCard, SectionHeader, TopBar, formatDate } from "@/components/app-shell";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface TRDContext {
  target_environment?: string;
  scalability_requirement?: string;
  security_level?: string;
  [key: string]: unknown;
}

interface TechStack {
  languages?: string[];
  frameworks?: string[];
  databases?: string[];
  infrastructure?: string[];
  rationale?: string;
  [key: string]: unknown;
}

interface ArchLayer {
  name: string;
  responsibility: string;
  components: string[];
}

interface ArchComponent {
  name: string;
  type: string;
  responsibility: string;
  interfaces: string[];
  dependencies: string[];
}

interface DataFlow {
  source: string;
  target: string;
  data: string;
  protocol: string;
}

interface SystemArchitecture {
  architecture_style?: string;
  layers?: ArchLayer[];
  components?: ArchComponent[];
  data_flow?: DataFlow[];
}

interface EntityField {
  name: string;
  type: string;
  constraints: string;
}

interface DBEntity {
  name: string;
  description: string;
  fields: EntityField[];
}

interface DatabaseDesign {
  entities?: DBEntity[];
}

interface APIEndpoint {
  path: string;
  method: string;
  description: string;
  request_schema?: Record<string, unknown>;
  response_schema?: Record<string, unknown>;
}

interface APISpecification {
  endpoints?: APIEndpoint[];
}

interface TRDMetadata {
  version?: string;
  status?: string;
  created_at?: string;
  source_prd_id?: string;
  source_prd_title?: string;
}

interface TRDData {
  title?: string;
  context?: TRDContext;
  technology_stack?: TechStack;
  system_architecture?: SystemArchitecture;
  database_design?: DatabaseDesign;
  api_specification?: APISpecification;
  metadata?: TRDMetadata;
}

/* ------------------------------------------------------------------ */
/*  Tabs                                                               */
/* ------------------------------------------------------------------ */

type TabKey = "overview" | "architecture" | "api" | "database";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "overview", label: "개요" },
  { key: "architecture", label: "시스템 아키텍처" },
  { key: "api", label: "API 명세" },
  { key: "database", label: "데이터베이스" },
];

const TRD_ACCENT = "#9065B0";

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function TRDViewerPage() {
  const params = useParams();
  const docId = params.id as string;
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [rawView, setRawView] = useState<"json" | "md" | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["trd-doc", docId],
    queryFn: () => api.getOutputDocument(docId, "json"),
  });

  const { data: mdData } = useQuery({
    queryKey: ["trd-doc-md", docId],
    queryFn: () => api.getOutputDocument(docId, "md"),
    enabled: rawView === "md",
  });

  const trd = (data?.content_json ?? {}) as TRDData;

  async function handleDownload(format: "json" | "md") {
    const result = await api.getOutputDocument(docId, format);
    const content = format === "json"
      ? JSON.stringify(result.content_json, null, 2)
      : (result.content_md ?? "");
    const blob = new Blob([content], { type: format === "json" ? "application/json" : "text/plain" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `trd-${docId}.${format === "json" ? "json" : "md"}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading) {
    return (
      <AppShell header={<TopBar title="TRD 상세" subtitle="문서를 불러오는 중입니다" href="/history" />}>
        <section className="section-card flex items-center justify-center py-20">
          <Loader2 className="h-10 w-10 animate-spin" style={{ color: TRD_ACCENT }} />
        </section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell header={<TopBar title="TRD 상세" subtitle="문서를 찾을 수 없습니다" href="/history" />}>
        <section className="section-card">
          <div className="flex flex-col items-center justify-center px-6 py-20 text-center">
            <AlertCircle className="h-10 w-10 text-[#E03E3E]" />
            <p className="mt-4 text-xl font-semibold tracking-tight text-slate-900">TRD를 불러오지 못했습니다</p>
            <Link href="/history" className="mt-6 brand-button">돌아가기</Link>
          </div>
        </section>
      </AppShell>
    );
  }

  const arch = trd.system_architecture ?? {};
  const dbDesign = trd.database_design ?? {};
  const apiSpec = trd.api_specification ?? {};

  return (
    <AppShell
      header={
        <TopBar
          title={trd.title ?? "TRD 문서"}
          subtitle={`${trd.metadata?.version ? `버전 ${trd.metadata.version} ` : ""}${trd.metadata?.created_at ? `${formatDate(trd.metadata.created_at)}` : ""}`}
          href="/history"
          action={
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setRawView(rawView === "json" ? null : "json")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Code2 className="h-4 w-4" /> JSON 보기
              </button>
              <button onClick={() => setRawView(rawView === "md" ? null : "md")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Code2 className="h-4 w-4" /> Markdown 보기
              </button>
              <button onClick={() => handleDownload("json")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Download className="h-4 w-4" /> JSON
              </button>
              <button onClick={() => handleDownload("md")} className="secondary-button !rounded-xl !px-3 !py-1.5">
                <Download className="h-4 w-4" /> MD
              </button>
            </div>
          }
        />
      }
    >
      {/* Raw view overlay */}
      {rawView ? (
        <section className="section-card">
          <SectionHeader
            title={rawView === "json" ? "JSON 원본" : "Markdown 원본"}
            action={
              <button onClick={() => setRawView(null)} className="secondary-button !rounded-xl !px-3 !py-1.5">닫기</button>
            }
          />
          <pre className="mt-4 max-h-[600px] overflow-auto rounded-xl bg-slate-50 p-5 text-xs leading-6 text-slate-700">
            {rawView === "json"
              ? JSON.stringify(trd, null, 2)
              : (mdData?.content_md ?? "Markdown 데이터를 불러오는 중입니다...")}
          </pre>
        </section>
      ) : null}

      {/* Metric cards */}
      <section className="grid gap-4 lg:grid-cols-4">
        <MetricCard label="아키텍처 레이어" value={arch.layers?.length ?? 0} note={arch.architecture_style ?? "정의되지 않음"} />
        <MetricCard label="컴포넌트" value={arch.components?.length ?? 0} note="시스템 구성 요소" accent="warm" />
        <MetricCard label="API 엔드포인트" value={apiSpec.endpoints?.length ?? 0} note="정의된 API 수" accent="mint" />
        <MetricCard label="DB 엔티티" value={dbDesign.entities?.length ?? 0} note="데이터베이스 테이블 수" />
      </section>

      {/* Tabs */}
      <section className="section-card">
        <div className="mb-6 flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`tab-button ${activeTab === tab.key ? "tab-button-active" : "tab-button-idle"}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "overview" ? <OverviewTab trd={trd} /> : null}
        {activeTab === "architecture" ? <ArchitectureTab arch={arch} /> : null}
        {activeTab === "api" ? <APITab apiSpec={apiSpec} /> : null}
        {activeTab === "database" ? <DatabaseTab dbDesign={dbDesign} /> : null}
      </section>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/*  Overview Tab                                                       */
/* ------------------------------------------------------------------ */

function OverviewTab({ trd }: { trd: TRDData }) {
  const ctx = trd.context ?? {};
  const stack = trd.technology_stack ?? {};

  const contextEntries = Object.entries(ctx).filter(([, v]) => v !== undefined && v !== null && v !== "");

  return (
    <div className="space-y-6">
      {/* Context */}
      {contextEntries.length > 0 ? (
        <div>
          <SectionHeader title="프로젝트 컨텍스트" description="대상 환경, 확장성 요구, 보안 수준 등" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {contextEntries.map(([key, value]) => (
              <div key={key} className="list-card" style={{ borderLeft: `3px solid ${TRD_ACCENT}` }}>
                <p className="data-label">{formatContextKey(key)}</p>
                <p className="mt-2 text-sm font-semibold text-slate-900">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Technology Stack */}
      <div>
        <SectionHeader title="기술 스택" description="프로젝트에 사용되는 기술 구성" />
        <div className="grid gap-4 sm:grid-cols-2">
          <TechStackCard title="언어" items={stack.languages} icon={<Code2 className="h-4 w-4" style={{ color: TRD_ACCENT }} />} />
          <TechStackCard title="프레임워크" items={stack.frameworks} icon={<Layers className="h-4 w-4" style={{ color: TRD_ACCENT }} />} />
          <TechStackCard title="데이터베이스" items={stack.databases} icon={<Database className="h-4 w-4" style={{ color: TRD_ACCENT }} />} />
          <TechStackCard title="인프라" items={stack.infrastructure} icon={<Server className="h-4 w-4" style={{ color: TRD_ACCENT }} />} />
        </div>
        {stack.rationale ? (
          <div className="mt-4 surface-muted p-5">
            <p className="data-label">기술 선택 근거</p>
            <p className="mt-3 text-sm leading-7 text-slate-700">{stack.rationale}</p>
          </div>
        ) : null}
      </div>

      {/* Source PRD link */}
      {trd.metadata?.source_prd_title ? (
        <div className="surface-muted p-5">
          <p className="data-label">원본 PRD</p>
          <p className="mt-2 text-sm font-semibold text-slate-900">{trd.metadata.source_prd_title}</p>
          {trd.metadata.source_prd_id ? (
            <p className="mt-1 text-xs text-slate-500">ID: {trd.metadata.source_prd_id}</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function TechStackCard({ title, items, icon }: { title: string; items?: string[]; icon: React.ReactNode }) {
  return (
    <div className="list-card">
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <p className="text-base font-semibold text-slate-900">{title}</p>
      </div>
      {items && items.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <span key={item} className="pill-badge bg-[#9065B0]/10 text-[#9065B0]">{item}</span>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-500">정의되지 않음</p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Architecture Tab                                                   */
/* ------------------------------------------------------------------ */

function ArchitectureTab({ arch }: { arch: SystemArchitecture }) {
  const [expandedComponents, setExpandedComponents] = useState<Set<string>>(new Set());

  function toggleComponent(name: string) {
    setExpandedComponents((current) => {
      const next = new Set(current);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  return (
    <div className="space-y-8">
      {/* Architecture style */}
      {arch.architecture_style ? (
        <div className="surface-muted p-5">
          <p className="data-label">아키텍처 스타일</p>
          <p className="mt-2 text-lg font-bold text-slate-900">{arch.architecture_style}</p>
        </div>
      ) : null}

      {/* Layers */}
      {arch.layers && arch.layers.length > 0 ? (
        <div>
          <SectionHeader title="레이어 구성" description="시스템의 계층 구조" />
          <div className="space-y-3">
            {arch.layers.map((layer, index) => (
              <div key={layer.name} className="list-card" style={{ borderLeft: `3px solid ${TRD_ACCENT}` }}>
                <div className="flex items-start gap-4">
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white"
                    style={{ background: TRD_ACCENT }}
                  >
                    L{index + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-base font-bold tracking-[-0.03em] text-slate-900">{layer.name}</p>
                    <p className="mt-1 text-sm leading-7 text-slate-600">{layer.responsibility}</p>
                    {layer.components.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {layer.components.map((comp) => (
                          <span key={comp} className="pill-badge bg-slate-100 text-slate-600">{comp}</span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Components */}
      {arch.components && arch.components.length > 0 ? (
        <div>
          <SectionHeader title="컴포넌트 상세" description="각 컴포넌트의 인터페이스와 의존성" />
          <div className="space-y-3">
            {arch.components.map((comp) => {
              const expanded = expandedComponents.has(comp.name);
              return (
                <div key={comp.name} className="rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel)]">
                  <button onClick={() => toggleComponent(comp.name)} className="flex w-full items-start gap-4 p-5 text-left">
                    <div className="mt-1 text-slate-400">
                      {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="pill-badge bg-[#9065B0]/10 text-[#9065B0]">{comp.type}</span>
                      </div>
                      <p className="mt-2 text-base font-semibold tracking-tight text-slate-900">{comp.name}</p>
                      <p className="mt-1 text-sm text-slate-600">{comp.responsibility}</p>
                    </div>
                  </button>
                  {expanded ? (
                    <div className="border-t border-[var(--line-soft)] px-5 pb-5 pl-14 pt-5">
                      <div className="grid gap-4 lg:grid-cols-2">
                        <div className="surface-muted p-4">
                          <p className="data-label">인터페이스</p>
                          {comp.interfaces.length > 0 ? (
                            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
                              {comp.interfaces.map((iface) => (
                                <li key={iface}>- {iface}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="mt-3 text-sm text-slate-500">없음</p>
                          )}
                        </div>
                        <div className="surface-muted p-4">
                          <p className="data-label">의존성</p>
                          {comp.dependencies.length > 0 ? (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {comp.dependencies.map((dep) => (
                                <span key={dep} className="pill-badge bg-slate-100 text-slate-600">{dep}</span>
                              ))}
                            </div>
                          ) : (
                            <p className="mt-3 text-sm text-slate-500">없음</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* Data Flow */}
      {arch.data_flow && arch.data_flow.length > 0 ? (
        <div>
          <SectionHeader title="데이터 플로우" description="시스템 간 데이터 흐름" />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left">
                  <th className="px-4 py-3 font-semibold text-slate-900">소스</th>
                  <th className="px-4 py-3 font-semibold text-slate-900">대상</th>
                  <th className="px-4 py-3 font-semibold text-slate-900">데이터</th>
                  <th className="px-4 py-3 font-semibold text-slate-900">프로토콜</th>
                </tr>
              </thead>
              <tbody>
                {arch.data_flow.map((flow, index) => (
                  <tr key={index} className="border-b border-slate-100">
                    <td className="px-4 py-3 font-medium text-slate-900">{flow.source}</td>
                    <td className="px-4 py-3 text-slate-700">
                      <div className="flex items-center gap-2">
                        <ArrowRightLeft className="h-3 w-3 text-slate-400" />
                        {flow.target}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{flow.data}</td>
                    <td className="px-4 py-3">
                      <span className="pill-badge bg-slate-100 text-slate-600">{flow.protocol}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Empty state */}
      {!arch.layers?.length && !arch.components?.length && !arch.data_flow?.length ? (
        <EmptyPanel title="아키텍처 정보가 없습니다" />
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  API Tab                                                            */
/* ------------------------------------------------------------------ */

const METHOD_STYLE: Record<string, string> = {
  GET: "bg-emerald-100 text-emerald-700",
  POST: "bg-blue-100 text-blue-700",
  PUT: "bg-orange-100 text-orange-700",
  PATCH: "bg-amber-100 text-amber-700",
  DELETE: "bg-rose-100 text-rose-700",
};

function APITab({ apiSpec }: { apiSpec: APISpecification }) {
  const [expandedEndpoints, setExpandedEndpoints] = useState<Set<number>>(new Set());

  function toggleEndpoint(index: number) {
    setExpandedEndpoints((current) => {
      const next = new Set(current);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }

  const endpoints = apiSpec.endpoints ?? [];

  if (!endpoints.length) {
    return <EmptyPanel title="API 명세가 없습니다" />;
  }

  return (
    <div className="space-y-3">
      <SectionHeader title="엔드포인트 목록" description={`총 ${endpoints.length}개의 API 엔드포인트`} />
      {endpoints.map((ep, index) => {
        const expanded = expandedEndpoints.has(index);
        const methodClass = METHOD_STYLE[ep.method.toUpperCase()] ?? "bg-slate-100 text-slate-600";
        return (
          <div key={index} className="rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel)]">
            <button onClick={() => toggleEndpoint(index)} className="flex w-full items-start gap-4 p-5 text-left">
              <div className="mt-1 text-slate-400">
                {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-3">
                  <span className={`pill-badge font-mono text-xs font-bold ${methodClass}`}>{ep.method.toUpperCase()}</span>
                  <code className="text-sm font-semibold text-slate-900">{ep.path}</code>
                </div>
                <p className="mt-2 text-sm text-slate-600">{ep.description}</p>
              </div>
            </button>
            {expanded ? (
              <div className="border-t border-[var(--line-soft)] px-5 pb-5 pl-14 pt-5">
                <div className="grid gap-4 lg:grid-cols-2">
                  {ep.request_schema && Object.keys(ep.request_schema).length > 0 ? (
                    <div className="surface-muted p-4">
                      <p className="data-label">요청 스키마</p>
                      <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-100 p-3 text-xs leading-5 text-slate-700">
                        {JSON.stringify(ep.request_schema, null, 2)}
                      </pre>
                    </div>
                  ) : null}
                  {ep.response_schema && Object.keys(ep.response_schema).length > 0 ? (
                    <div className="surface-muted p-4">
                      <p className="data-label">응답 스키마</p>
                      <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-100 p-3 text-xs leading-5 text-slate-700">
                        {JSON.stringify(ep.response_schema, null, 2)}
                      </pre>
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Database Tab                                                       */
/* ------------------------------------------------------------------ */

function DatabaseTab({ dbDesign }: { dbDesign: DatabaseDesign }) {
  const [expandedEntities, setExpandedEntities] = useState<Set<string>>(new Set());

  function toggleEntity(name: string) {
    setExpandedEntities((current) => {
      const next = new Set(current);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  const entities = dbDesign.entities ?? [];

  if (!entities.length) {
    return <EmptyPanel title="데이터베이스 설계 정보가 없습니다" />;
  }

  return (
    <div className="space-y-3">
      <SectionHeader title="엔티티 목록" description={`총 ${entities.length}개의 데이터 엔티티`} />
      {entities.map((entity) => {
        const expanded = expandedEntities.has(entity.name);
        return (
          <div key={entity.name} className="rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel)]">
            <button onClick={() => toggleEntity(entity.name)} className="flex w-full items-start gap-4 p-5 text-left">
              <div className="mt-1 text-slate-400">
                {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Box className="h-4 w-4" style={{ color: TRD_ACCENT }} />
                  <p className="text-base font-semibold tracking-tight text-slate-900">{entity.name}</p>
                </div>
                <p className="mt-1 text-sm text-slate-600">{entity.description}</p>
                <p className="mt-1 text-xs text-slate-400">{entity.fields?.length ?? 0}개 필드</p>
              </div>
            </button>
            {expanded && entity.fields?.length ? (
              <div className="border-t border-[var(--line-soft)] p-5 pl-14">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 text-left">
                        <th className="px-3 py-2 font-semibold text-slate-900">필드명</th>
                        <th className="px-3 py-2 font-semibold text-slate-900">타입</th>
                        <th className="px-3 py-2 font-semibold text-slate-900">제약조건</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entity.fields.map((field) => (
                        <tr key={field.name} className="border-b border-slate-100">
                          <td className="px-3 py-2 font-mono text-xs font-medium text-slate-900">{field.name}</td>
                          <td className="px-3 py-2">
                            <span className="pill-badge bg-[#9065B0]/10 text-[#9065B0]">{field.type}</span>
                          </td>
                          <td className="px-3 py-2 text-slate-600">{field.constraints || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Utilities                                                          */
/* ------------------------------------------------------------------ */

function EmptyPanel({ title }: { title: string }) {
  return (
    <div className="surface-muted flex items-center justify-center rounded-2xl px-6 py-16 text-center">
      <p className="text-base font-semibold text-slate-700">{title}</p>
    </div>
  );
}

function formatContextKey(key: string): string {
  const labels: Record<string, string> = {
    target_environment: "대상 환경",
    scalability_requirement: "확장성 요구사항",
    security_level: "보안 수준",
  };
  return labels[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
