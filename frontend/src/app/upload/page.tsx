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
import { AppShell, SectionHeader, TopBar } from "@/components/app-shell";

const FILE_TYPE_CONFIG: Record<string, { icon: typeof FileText; label: string }> = {
  txt: { icon: FileText, label: "텍스트" },
  md: { icon: FileText, label: "마크다운" },
  eml: { icon: Mail, label: "이메일" },
  msg: { icon: Mail, label: "이메일" },
  xlsx: { icon: Table, label: "스프레드시트" },
  xls: { icon: Table, label: "스프레드시트" },
  csv: { icon: Table, label: "CSV" },
  pptx: { icon: Presentation, label: "PPT" },
  ppt: { icon: Presentation, label: "PPT" },
  png: { icon: Image, label: "이미지" },
  jpg: { icon: Image, label: "이미지" },
  jpeg: { icon: Image, label: "이미지" },
  pdf: { icon: FileEdit, label: "PDF" },
  docx: { icon: FileEdit, label: "워드" },
  doc: { icon: FileEdit, label: "워드" },
  json: { icon: MessageCircle, label: "채팅 로그" },
};

function getFileConfig(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  return FILE_TYPE_CONFIG[ext] ?? { icon: FileText, label: "파일" };
}

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
      const documents = Array.isArray(uploadResult?.documents) ? uploadResult.documents : [];
      const documentIds = documents.map((document) => document?.id).filter(Boolean) as string[];

      setUploading(false);
      setProcessing(true);

      const processResult = await api.startProcessing(documentIds);
      const jobId = processResult?.job_id;
      if (!jobId) throw new Error("서버에서 작업 ID를 받지 못했습니다.");
      router.push(`/processing/${jobId}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "업로드에 실패했습니다.");
      setUploading(false);
      setProcessing(false);
    }
  }

  return (
    <AppShell header={<TopBar title="새 문서 업로드" subtitle="원본 문서를 한 번에 모아 생성 파이프라인을 시작합니다." />}>
      <section className="section-card">
        <span className="inline-flex items-center gap-2 rounded-full border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
          Upload Intake
        </span>
        <h2 className="mt-5 max-w-[12ch] text-4xl font-semibold tracking-[-0.06em] text-slate-900">
          필요한 파일만 담고 바로 시작합니다
        </h2>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
          업로드 화면은 입력과 실행만 남겼습니다. 파일을 추가하고, 큐를 확인한 뒤, 바로 생성 흐름으로 넘기는 데 집중합니다.
        </p>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <UploadSummaryCard label="선택 파일" value={`${summary.count}개`} note="현재 업로드 큐에 담긴 파일 수" />
          <UploadSummaryCard label="총 용량" value={`${summary.totalMb} MB`} note="선택 파일 전체 용량" />
          <UploadSummaryCard label="지원 포맷" value={`${Object.keys(FILE_TYPE_CONFIG).length}종`} note="업무 문서 기준으로 정리된 입력 범위" />
        </div>
      </section>

      <section className="grid gap-6">
        <section className="section-card">
          <SectionHeader title="문서 드롭존" description="파일을 끌어 놓거나 클릭해서 선택하세요. 중복 문서는 자동으로 제외됩니다." />
          <div
            {...getRootProps()}
            className={`rounded-[1.5rem] border border-dashed px-8 py-14 text-center transition ${
              isDragActive
                ? "border-[var(--accent-strong)] bg-[rgba(25,74,119,0.05)]"
                : "border-[var(--line-strong)] bg-[var(--bg-panel-muted)] hover:border-[rgba(25,74,119,0.3)] hover:bg-[var(--bg-panel)]"
            }`}
          >
            <input {...getInputProps()} />
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[1.25rem] bg-[#17212b] text-white shadow-lg">
              <Upload className="h-6 w-6" />
            </div>
            <p className="mt-5 text-2xl font-semibold tracking-[-0.04em] text-slate-900">
              {isDragActive ? "여기에 파일을 놓아주세요" : "파일을 드래그하거나 클릭해 추가하세요"}
            </p>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-500">
              TXT, MD, CSV, XLSX, PPTX, PDF, DOCX, PNG, JPG, JSON 채팅 로그까지 한 번에 담을 수 있습니다.
            </p>
          </div>

          {error ? (
            <div className="mt-4 rounded-[1rem] border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-700">
              {error}
            </div>
          ) : null}
        </section>

        <section className="section-card">
          <SectionHeader
            title="업로드 큐"
            description={files.length ? `${files.length}개 파일이 생성 대기 상태입니다.` : "아직 선택된 파일이 없습니다."}
          />

          {files.length ? (
            <div className="space-y-3">
              {files.map((file, index) => {
                const config = getFileConfig(file.name);
                const Icon = config.icon;

                return (
                  <div key={`${file.name}-${file.size}-${index}`} className="list-card">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex min-w-0 items-center gap-4">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] text-slate-700">
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-base font-semibold text-slate-900">{file.name}</p>
                          <p className="mt-1 text-sm text-slate-500">
                            {config.label} · {(file.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      <button onClick={() => removeFile(index)} className="secondary-button secondary-button-icon">
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="rounded-[1.4rem] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-6 py-16 text-center">
              <p className="text-base font-semibold text-slate-900">선택된 파일이 없습니다</p>
              <p className="mt-2 text-sm text-slate-500">위 드롭존에 문서를 추가하면 여기서 바로 확인할 수 있습니다.</p>
            </div>
          )}
        </section>
      </section>

      <div className="h-24" aria-hidden="true" />

      <div className="fixed bottom-4 left-1/2 z-40 w-[calc(100%-2rem)] max-w-5xl -translate-x-1/2">
        <div className="glass-panel-strong flex flex-col gap-4 rounded-[1.4rem] px-5 py-4 shadow-[0_16px_48px_rgba(0,0,0,0.18)] md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <p className="data-label">선택 파일</p>
              <p className="mt-1 text-lg font-semibold tracking-[-0.03em] text-slate-900">{summary.count}개</p>
            </div>
            <div>
              <p className="data-label">총 용량</p>
              <p className="mt-1 text-lg font-semibold tracking-[-0.03em] text-slate-900">{summary.totalMb} MB</p>
            </div>
          </div>

          <button
            onClick={handleUploadAndProcess}
            disabled={!files.length || uploading || processing}
            className="brand-button disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading || processing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {uploading ? "업로드 중" : processing ? "작업 시작 중" : "생성 시작"}
          </button>
        </div>
      </div>
    </AppShell>
  );
}

function UploadSummaryCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-[22px] border border-[var(--line-soft)] bg-[var(--bg-panel-muted)] px-4 py-4">
      <p className="data-label">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-slate-900">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{note}</p>
    </div>
  );
}
