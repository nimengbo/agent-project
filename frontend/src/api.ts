const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export type PublicModelConfig = {
  configured: boolean;
  base_url: string;
  chat_model: string;
  reasoner_model: string;
  api_key_preview?: string;
};

export type ModelConfigPayload = {
  api_key: string;
  base_url: string;
  chat_model: string;
  reasoner_model: string;
};

export type UploadedDocumentResponse = {
  document_id: string;
  filename?: string | null;
  content_type?: string | null;
  size?: number;
  chunk_count?: number;
  indexed_chunks?: number;
  status?: string;
  metadata?: Record<string, unknown>;
};

export type ChatMessagePayload = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

export type InterviewReport = {
  interview_id: string;
  summary: string;
  scores: Record<string, number>;
  recommendations: string[];
};

async function readJson<T>(response: Response, fallbackMessage: string): Promise<T> {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail ?? fallbackMessage);
  }
  return payload as T;
}

export async function getModelConfig(): Promise<PublicModelConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config/model`);
  return readJson<PublicModelConfig>(response, '读取模型配置失败');
}

export async function saveModelConfig(payload: ModelConfigPayload): Promise<PublicModelConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config/model`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return readJson<PublicModelConfig>(response, '保存模型配置失败');
}

export async function sendInterviewMessage(payload: {
  content: string;
  conversation: ChatMessagePayload[];
  documentIds: string[];
}): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/interviews/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: payload.content,
      position: '移动端架构师',
      difficulty: 'senior',
      conversation: formatConversation(payload.conversation),
      document_ids: payload.documentIds,
    }),
  });
  const result = await readJson<{ content: string }>(response, '发送失败');
  return result.content;
}

export async function generateInterviewReport(payload: {
  interviewId: string;
  conversation: ChatMessagePayload[];
  documentIds: string[];
}): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/reports/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      interview_id: payload.interviewId,
      position: '移动端架构师',
      difficulty: 'senior',
      conversation: formatConversation(payload.conversation),
      document_ids: payload.documentIds,
    }),
  });
  const result = await readJson<{ content: string }>(response, '生成报告失败');
  return result.content;
}

function formatConversation(messages: ChatMessagePayload[]): string {
  return messages
    .filter((message) => message.role !== 'system' && message.content.trim())
    .map((message) => `${message.role === 'user' ? '候选人' : '面试官'}：${message.content.trim()}`)
    .join('\n');
}

export async function uploadDocument(file: File): Promise<UploadedDocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  return readJson<UploadedDocumentResponse>(response, '上传失败');
}

export async function getInterviewReport(interviewId: string): Promise<InterviewReport> {
  const response = await fetch(`${API_BASE_URL}/api/reports/${interviewId}`);
  return readJson<InterviewReport>(response, '读取报告失败');
}
