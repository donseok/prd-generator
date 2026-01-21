"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileText,
  Mail,
  Table,
  Presentation,
  Image,
  MessageCircle,
  FileEdit,
  X,
  Loader2,
  ArrowLeft,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

const FILE_TYPE_CONFIG: Record<string, { icon: typeof FileText; label: string; color: string }> = {
  txt: { icon: FileText, label: "텍스트", color: "bg-gray-500" },
  md: { icon: FileText, label: "마크다운", color: "bg-gray-500" },
  eml: { icon: Mail, label: "이메일", color: "bg-blue-500" },
  msg: { icon: Mail, label: "이메일", color: "bg-blue-500" },
  xlsx: { icon: Table, label: "엑셀", color: "bg-green-500" },
  xls: { icon: Table, label: "엑셀", color: "bg-green-500" },
  csv: { icon: Table, label: "CSV", color: "bg-green-500" },
  pptx: { icon: Presentation, label: "PPT", color: "bg-orange-500" },
  ppt: { icon: Presentation, label: "PPT", color: "bg-orange-500" },
  png: { icon: Image, label: "이미지", color: "bg-purple-500" },
  jpg: { icon: Image, label: "이미지", color: "bg-purple-500" },
  jpeg: { icon: Image, label: "이미지", color: "bg-purple-500" },
  pdf: { icon: FileEdit, label: "PDF", color: "bg-red-500" },
  docx: { icon: FileEdit, label: "Word", color: "bg-indigo-500" },
  doc: { icon: FileEdit, label: "Word", color: "bg-indigo-500" },
  json: { icon: MessageCircle, label: "채팅", color: "bg-yellow-500" },
};

function getFileConfig(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  return FILE_TYPE_CONFIG[ext] || { icon: FileText, label: "파일", color: "bg-slate-500" };
}

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);
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

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadAndProcess = async () => {
    if (files.length === 0) return;

    try {
      setUploading(true);
      setError(null);

      // Upload files
      const uploadResult = await api.uploadFiles(files);
      const documentIds = uploadResult.documents.map((d) => d.id);

      setUploading(false);
      setProcessing(true);

      // Start processing
      const processResult = await api.startProcessing(documentIds);

      // Navigate to processing status page
      router.push(`/processing/${processResult.job_id}`);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "업로드 실패";
      setError(errorMessage);
      setUploading(false);
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-4">
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
                <h1 className="text-lg font-bold">새 PRD 생성</h1>
                <p className="text-xs text-slate-400">문서 업로드</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
            ${isDragActive
              ? "border-blue-500 bg-blue-500/10"
              : "border-slate-600 hover:border-slate-500 hover:bg-slate-800/50"
            }
          `}
        >
          <input {...getInputProps()} />
          <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragActive ? "text-blue-400" : "text-slate-400"}`} />
          <p className="text-lg font-medium mb-2">
            {isDragActive ? "여기에 놓으세요" : "파일을 드래그하거나 클릭하여 선택"}
          </p>
          <p className="text-sm text-slate-400">
            지원 형식: TXT, MD, EML, XLSX, CSV, PPTX, PDF, DOCX, PNG, JPG, JSON
          </p>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-slate-300 mb-3">
              선택된 파일 ({files.length}개)
            </h3>
            <div className="space-y-2">
              {files.map((file, index) => {
                const config = getFileConfig(file.name);
                const Icon = config.icon;
                return (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${config.color}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{file.name}</p>
                        <p className="text-xs text-slate-400">
                          {config.label} · {(file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="p-1 hover:bg-slate-700 rounded transition-colors"
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Action Button */}
        <div className="mt-8 flex justify-end">
          <button
            onClick={handleUploadAndProcess}
            disabled={files.length === 0 || uploading || processing}
            className={`
              flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all
              ${files.length === 0 || uploading || processing
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-500 text-white"
              }
            `}
          >
            {uploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                업로드 중...
              </>
            ) : processing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                처리 시작 중...
              </>
            ) : (
              <>
                <Layers className="w-5 h-5" />
                PRD 생성 시작
              </>
            )}
          </button>
        </div>

        {/* Info */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700">
            <h4 className="font-medium mb-2 text-blue-400">지원 입력 형식</h4>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• 텍스트/마크다운 (TXT, MD)</li>
              <li>• 이메일 (EML)</li>
              <li>• 스프레드시트 (XLSX, CSV)</li>
              <li>• 프레젠테이션 (PPTX)</li>
              <li>• 문서 (PDF, DOCX)</li>
              <li>• 이미지 (PNG, JPG)</li>
              <li>• 채팅 로그 (JSON)</li>
            </ul>
          </div>
          <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700">
            <h4 className="font-medium mb-2 text-purple-400">처리 과정</h4>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>1. 파싱: 파일에서 텍스트 추출</li>
              <li>2. 정규화: 요구사항 분류 및 변환</li>
              <li>3. 검증: 품질 확인 (80% 이상 자동 승인)</li>
              <li>4. 생성: PRD 문서 자동 작성</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
