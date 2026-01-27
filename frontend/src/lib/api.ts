import axios from "axios";

// API 서버 주소 (환경변수 또는 기본값)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

// Axios 클라이언트 설정
const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * 데이터 타입 정의
 * 서버와 주고받는 데이터의 구조를 정의합니다.
 */

// PRD 요약 정보
export interface PRDSummary {
  id: string;
  title: string;
  status: string;
  overall_confidence: number;
  requires_pm_review: boolean;
  created_at: string;
  requirements_count: number;
}

// 작업 요약 정보
export interface JobSummary {
  job_id: string;
  status: string;
  documents: string[];
  prd_id: string | null;
  requires_pm_review: boolean;
  created_at: string;
}

// PRD 목록 응답 구조
export interface PRDListResponse {
  total: number;
  prds: PRDSummary[];
}

// 작업 목록 응답 구조
export interface JobListResponse {
  total: number;
  jobs: JobSummary[];
}

// 작업 상태 정보
export interface ProcessingStatus {
  job_id: string;
  status: string;
  current_layer: string;
  completed_layers: number;
  total_layers: number;
  progress_percent: number;
  requires_pm_review: boolean;
  pending_reviews: number;
  documents: string[];
  prd_id: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

// 검토 항목 정보
export interface ReviewItem {
  id: string;
  requirement_id: string;
  issue_type: string;
  description: string;
  original_text: string;
  suggested_resolution: string | null;
  created_at: string;
}

// 대기 중인 검토 목록 응답 구조
export interface PendingReviewsResponse {
  job_id: string;
  status: string;
  total_items: number;
  pending_count: number;
  resolved_count: number;
  pending_items: ReviewItem[];
  resolved_items: Array<{
    id: string;
    requirement_id: string;
    decision: string;
    resolved_at: string | null;
  }>;
}

// 하위 호환성을 위한 타입 별칭
export type PRDListItem = PRDSummary;
export type ProcessingJob = JobSummary;

export interface Requirement {
  id: string;
  type: "FR" | "NFR" | "CONSTRAINT";
  title: string;
  description: string;
  user_story?: string;
  acceptance_criteria: string[];
  priority: "HIGH" | "MEDIUM" | "LOW";
  confidence_score: number;
  confidence_reason: string;
  source_reference: string;
  assumptions: string[];
  missing_info: string[];
  related_requirements: string[];
}

/**
 * API 호출 함수 모음
 */
export const api = {
  // === PRD 관련 API ===
  
  // PRD 목록 조회
  async listPRDs(skip = 0, limit = 20, status?: string): Promise<PRDListResponse> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.append("status", status);
    const response = await client.get(`/prd?${params}`);
    return response.data;
  },

  // PRD 상세 조회
  async getPRD(prdId: string) {
    const response = await client.get(`/prd/${prdId}`);
    return response.data;
  },

  // PRD 삭제
  async deletePRD(prdId: string) {
    const response = await client.delete(`/prd/${prdId}`);
    return response.data;
  },

  // PRD 내보내기 (다운로드)
  async exportPRD(prdId: string, format: "markdown" | "json" | "html" = "markdown") {
    const response = await client.get(`/prd/${prdId}/export?format=${format}`, {
      responseType: "blob",
    });
    return response.data;
  },

  // === 문서 업로드 관련 API ===

  // 단일 문서 업로드
  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append("files", file);  // 서버는 files(복수형) 키를 기대함
    const response = await client.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  // 다중 문서 업로드
  async uploadFiles(files: File[]): Promise<{ documents: Array<{ id: string; filename: string }> }> {
    const formData = new FormData();

    // 여러 파일을 files 키로 추가
    for (const file of files) {
      formData.append("files", file);
    }

    const response = await client.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    return {
      documents: response.data.documents.map((doc: { id: string; filename: string }) => ({
        id: doc.id,
        filename: doc.filename,
      })),
    };
  },

  // 텍스트 직접 입력 업로드
  async uploadText(text: string, title?: string) {
    const response = await client.post("/documents/text", { text, title });
    return response.data;
  },

  // === 처리(Processing) 작업 관련 API ===

  // 작업 목록 조회
  async listJobs(skip = 0, limit = 20, status?: string): Promise<JobListResponse> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.append("status", status);
    const response = await client.get(`/processing?${params}`);
    return response.data;
  },

  // 처리 시작 (파이프라인 실행)
  async startProcessing(documentIds: string[]) {
    const response = await client.post("/processing/start", { document_ids: documentIds });
    return response.data;
  },

  // 작업 상태 조회
  async getProcessingStatus(jobId: string): Promise<ProcessingStatus> {
    const response = await client.get(`/processing/status/${jobId}`);
    return response.data;
  },

  // 작업 취소
  async cancelProcessing(jobId: string) {
    const response = await client.post(`/processing/cancel/${jobId}`);
    return response.data;
  },

  // === 리뷰(Review) 관련 API ===

  // 대기 중인 리뷰 항목 조회
  async getPendingReviews(jobId: string): Promise<PendingReviewsResponse> {
    const response = await client.get(`/review/pending/${jobId}`);
    return response.data;
  },

  // 리뷰 결정 제출 (승인/반려/수정)
  async submitReviewDecision(
    jobId: string,
    reviewItemId: string,
    decision: "approve" | "reject" | "modify",
    notes?: string,
    modifiedContent?: Record<string, unknown>
  ) {
    const response = await client.post("/review/decision", {
      job_id: jobId,
      review_item_id: reviewItemId,
      decision,
      notes,
      modified_content: modifiedContent,
    });
    return response.data;
  },

  // 리뷰 완료 및 처리 재개
  async completeReview(jobId: string) {
    const response = await client.post(`/review/complete/${jobId}`);
    return response.data;
  },

  // 리뷰 통계 조회
  async getReviewStats(jobId: string) {
    const response = await client.get(`/review/stats/${jobId}`);
    return response.data;
  },

  // === 시스템 관련 API ===

  // 서버 상태 확인
  async healthCheck() {
    const response = await client.get("/health");
    return response.data;
  },
};

export default api;