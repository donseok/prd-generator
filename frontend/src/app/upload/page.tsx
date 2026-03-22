"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import {
  FileEdit,
  FileText,
  Image,
  Loader2,
  Mail,
  MessageCircle,
  Presentation,
  Sparkles,
  Table,
  Upload,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { AppShell, HeroPanel, SectionHeader, TopBar } from "@/components/app-shell";

const FILE_TYPE_CONFIG: Record<string, { icon: typeof FileText; label: string; color: string }> = {
  txt: { icon: FileText, label: "텍스트", color: "bg-gradient-to-br from-slate-500 to-slate-600" },
  md: { icon: FileText, label: "마크다운", color: "bg-gradient-to-br from-slate-500 to-slate-600" },
  eml: { icon: Mail, label: "이메일", color: "bg-gradient-to-br from-indigo-500 to-indigo-600" },
  msg: { icon: Mail, label: "이메일", color: "bg-gradient-to-br from-indigo-500 to-indigo-600" },
  xlsx: { icon: Table, label: "스프레드시트", color: "bg-gradient-to-br from-emerald-500 to-teal-600" },
  xls: { icon: Table, label: "스프레드시트", color: "bg-gradient-to-br from-emerald-500 to-teal-600" },
  csv: { icon: Table, label: "CSV", color: "bg-gradient-to-br from-emerald-500 to-teal-600" },
  pptx: { icon: Presentation, label: "PPT", color: "bg-gradient-to-br from-amber-500 to-orange-500" },
  ppt: { icon: Presentation, label: "PPT", color: "bg-gradient-to-br from-amber-500 to-orange-500" },
  png: { icon: Image, label: "이미지", color: "bg-gradient-to-br from-violet-500 to-purple-600" },
  jpg: { icon: Image, label: "이미지", color: "bg-gradient-to-br from-violet-500 to-purple-600" },
  jpeg: { icon: Image, label: "이미지", color: "bg-gradient-to-br from-violet-500 to-purple-600" },
  pdf: { icon: FileEdit, label: "PDF", color: "bg-gradient-to-br from-rose-500 to-red-500" },
  docx: { icon: FileEdit, label: "워드", color: "bg-gradient-to-br from-blue-500 to-indigo-600" },
  doc: { icon: FileEdit, label: "워드", color: "bg-gradient-to-br from-blue-500 to-indigo-600" },
  json: { icon: MessageCircle, label: "채팅 로그", color: "bg-gradient-to-br from-cyan-500 to-teal-500" },
};

function getFileConfig(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  return FILE_TYPE_CONFIG[ext] ?? { icon: FileText, label: "파일", color: "bg-gradient-to-br from-slate-500 to-slate-600" };
}

const FORMAT_CATEGORIES = [
  { label: "텍스트 및 마크다운", borderColor: "#6366F1" },
  { label: "이메일", borderColor: "#6366F1" },
  { label: "스프레드시트", borderColor: "#10B981" },
  { label: "발표 자료", borderColor: "#F59E0B" },
  { label: "PDF 및 워드", borderColor: "#8B5CF6" },
  { label: "이미지", borderColor: "#8B5CF6" },
  { label: "JSON 채팅 로그", borderColor: "#06B6D4" },
];

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => {
      const existing = new Set(prev.map((file) => `${file.name}-${file.size}`));
      const deduped = acceptedFiles.filter((file) => !existing.has(`${file.name}-${file.size}`));
      return [...prev, ...deduped];
    });
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/*": [".txt", ".md", ".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-powerpoint": [".ppt"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "message/rfc822": [".eml"],
      "image/*": [".png", ".jpg", ".jpeg"],
      "application/json": [".json"],
    },
  });

  const summary = useMemo(
    () => ({
      count: files.length,
      totalMb: (files.reduce((sum, file) => sum + file.size, 0) / 1024 / 1024).toFixed(2),
    }),
    [files]
  );

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, currentIndex) => currentIndex !== index));
  }

  async function handleUploadAndProcess() {
    if (!files.length) return;

    try {
      setUploading(true);
      setError(null);

      const uploadResult = await api.uploadFiles(files);
      const documentIds = uploadResult.documents.map((document) => document.id);

      setUploading(false);
      setProcessing(true);

      const processResult = await api.startProcessing(documentIds);
      router.push(`/processing/${processResult.job_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "업로드에 실패했습니다.");
      setUploading(false);
      setProcessing(false);
    }
  }

  return (
    <AppShell header={<TopBar title="새 PRD 등록" subtitle="원본 문서를 올리고 생성 흐름을 시작합니다." />}>
      <HeroPanel
        kicker="입력 수집"
        title="여러 문서를 한 번에 모아서 PRD 생성 흐름으로 넘깁니다"
        description="입력 형식이 달라도 한 화면에서 수집하고, 중복 파일은 자동으로 걸러지도록 업로드 경험을 다시 다듬었습니다. 파일을 모은 뒤 즉시 처리 파이프라인으로 이동합니다."
        actions={
          <button
            onClick={handleUploadAndProcess}
            disabled={!files.length || uploading || processing}
            className="brand-button disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading || processing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {uploading ? "업로드 중" : processing ? "작업 시작 중" : "생성 시작"}
          </button>
        }
        aside={
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="surface-muted p-4">
              <p className="data-label">파일 수</p>
              <p className="mt-2 text-3xl font-bold tracking-[-0.04em] text-[#6366F1]">{summary.count}</p>
            </div>
            <div className="surface-muted p-4">
              <p className="data-label">총 용량</p>
              <p className="mt-2 text-3xl font-bold tracking-[-0.04em] text-[#8B5CF6]">{summary.totalMb}</p>
              <p className="text-xs text-slate-500">MB</p>
            </div>
          </div>
        }
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="section-card">
          <SectionHeader title="문서 드롭존" description="파일을 끌어 놓거나 클릭해서 선택하세요. 중복 파일은 자동으로 제외됩니다." />
          <div
            {...getRootProps()}
            className={`relative overflow-hidden rounded-2xl border-2 border-dashed px-8 py-14 text-center transition-all duration-300 ${
              isDragActive
                ? "border-[#6366F1] bg-[#6366F1]/5 scale-[1.01]"
                : "border-[var(--line-strong)] bg-gradient-to-b from-[var(--bg-panel)] to-[var(--bg-panel-muted)] hover:border-[#6366F1]/50 hover:shadow-[0_0_30px_rgba(99,102,241,0.08)]"
            }`}
          >
            <input {...getInputProps()} />
            <div className="mx-auto flex h-[72px] w-[72px] items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-[0_4px_14px_rgba(99,102,241,0.25)]">
              <Upload className="h-7 w-7" />
            </div>
            <p className="mt-5 text-xl font-bold tracking-[-0.03em] text-slate-900">
              {isDragActive ? "여기에 파일을 놓아주세요" : "파일을 드래그하거나 클릭해 추가하세요"}
            </p>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-500">
              TXT, MD, EML, XLSX, CSV, PPTX, PDF, DOCX, PNG, JPG, JSON 형식을 한 번에 올릴 수 있습니다.
            </p>
          </div>

          {error ? <div className="mt-4 rounded-xl border border-[#F43F5E]/20 bg-[#F43F5E]/5 px-4 py-3 text-sm text-[#F43F5E]">{error}</div> : null}

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <FlowStep title="1. 수집" body="여러 원본 문서를 하나의 입력 세트로 묶습니다." index={0} />
            <FlowStep title="2. 정규화" body="텍스트와 구조를 읽어 요구사항 후보를 정리합니다." index={1} />
            <FlowStep title="3. 생성" body="검토 흐름을 거쳐 최종 PRD와 산출물을 만듭니다." index={2} />
          </div>

          {files.length ? (
            <div className="mt-8">
              <SectionHeader title="업로드 큐" description={`${files.length}개 파일이 생성 대기 상태입니다.`} />
              <div className="space-y-3">
                {files.map((file, index) => {
                  const config = getFileConfig(file.name);
                  const Icon = config.icon;

                  return (
                    <div key={`${file.name}-${file.size}-${index}`} className="list-card">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex min-w-0 items-center gap-4">
                          <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${config.color} text-white shadow-sm`}>
                            <Icon className="h-5 w-5" />
                          </div>
                          <div className="min-w-0">
                            <p className="truncate text-base font-semibold text-slate-900">{file.name}</p>
                            <p className="mt-1 text-sm text-slate-500">
                              {config.label} · {(file.size / 1024).toFixed(1)} KB
                            </p>
                          </div>
                        </div>
                        <button onClick={() => removeFile(index)} className="secondary-button !h-9 !w-9 !rounded-md !p-0">
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>

        <aside className="section-card stagger-in">
          <SectionHeader title="지원 입력 형식" description="업무에서 자주 섞이는 문서 조합을 기준으로 정리했습니다." />
          <div className="grid gap-3">
            {FORMAT_CATEGORIES.map((item) => (
              <div
                key={item.label}
                className="surface-muted px-4 py-4 text-sm font-semibold text-slate-700"
                style={{ borderLeft: `3px solid ${item.borderColor}` }}
              >
                {item.label}
              </div>
            ))}
          </div>

          <div className="mt-6 surface-muted p-5">
            <p className="data-label">현재 흐름</p>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              파일을 추가하면 목록에 즉시 반영되고, 업로드 완료 후에는 처리 상태 화면으로 자동 이동합니다.
            </p>
          </div>
        </aside>
      </section>
    </AppShell>
  );
}

function FlowStep({ title, body, index }: { title: string; body: string; index?: number }) {
  const colors = ["#6366F1", "#8B5CF6", "#10B981"];
  const color = colors[(index ?? 0) % 3];
  return (
    <div className="surface-muted p-5" style={{ borderTop: `3px solid ${color}` }}>
      <p className="data-label">{title}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{body}</p>
    </div>
  );
}
