import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface PRDSummary {
  id: string;
  title: string;
  status: string;
  overall_confidence: number;
  requires_pm_review: boolean;
  created_at: string;
  requirements_count: number;
}

export interface JobSummary {
  job_id: string;
  status: string;
  documents: string[];
  prd_id: string | null;
  requires_pm_review: boolean;
  created_at: string;
}

export interface PRDListResponse {
  total: number;
  prds: PRDSummary[];
}

export interface JobListResponse {
  total: number;
  jobs: JobSummary[];
}

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

export interface ReviewItem {
  id: string;
  requirement_id: string;
  issue_type: string;
  description: string;
  original_text: string;
  suggested_resolution: string | null;
  created_at: string;
}

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

// Type aliases for backward compatibility
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

export const api = {
  // PRD endpoints
  async listPRDs(skip = 0, limit = 20, status?: string): Promise<PRDListResponse> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.append("status", status);
    const response = await client.get(`/prd?${params}`);
    return response.data;
  },

  async getPRD(prdId: string) {
    const response = await client.get(`/prd/${prdId}`);
    return response.data;
  },

  async deletePRD(prdId: string) {
    const response = await client.delete(`/prd/${prdId}`);
    return response.data;
  },

  async exportPRD(prdId: string, format: "markdown" | "json" | "html" = "markdown") {
    const response = await client.get(`/prd/${prdId}/export?format=${format}`, {
      responseType: "blob",
    });
    return response.data;
  },

  // Document endpoints
  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append("files", file);  // Backend expects "files" (plural)
    const response = await client.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  async uploadFiles(files: File[]): Promise<{ documents: Array<{ id: string; filename: string }> }> {
    const formData = new FormData();

    // Backend expects "files" (plural) parameter with multiple files
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

  async uploadText(text: string, title?: string) {
    const response = await client.post("/documents/text", { text, title });
    return response.data;
  },

  // Processing endpoints
  async listJobs(skip = 0, limit = 20, status?: string): Promise<JobListResponse> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.append("status", status);
    const response = await client.get(`/processing?${params}`);
    return response.data;
  },

  async startProcessing(documentIds: string[]) {
    const response = await client.post("/processing/start", { document_ids: documentIds });
    return response.data;
  },

  async getProcessingStatus(jobId: string): Promise<ProcessingStatus> {
    const response = await client.get(`/processing/status/${jobId}`);
    return response.data;
  },

  async cancelProcessing(jobId: string) {
    const response = await client.post(`/processing/cancel/${jobId}`);
    return response.data;
  },

  // Review endpoints
  async getPendingReviews(jobId: string): Promise<PendingReviewsResponse> {
    const response = await client.get(`/review/pending/${jobId}`);
    return response.data;
  },

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

  async completeReview(jobId: string) {
    const response = await client.post(`/review/complete/${jobId}`);
    return response.data;
  },

  async getReviewStats(jobId: string) {
    const response = await client.get(`/review/stats/${jobId}`);
    return response.data;
  },

  // Health check
  async healthCheck() {
    const response = await client.get("/health");
    return response.data;
  },
};

export default api;
