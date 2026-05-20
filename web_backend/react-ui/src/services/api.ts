/**
 * API Service for communicating with backend
 * Handles file upload, transcription, and summary generation
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface MeetingUploadResponse {
  success: boolean;
  meeting_id: string;
  file_name: string;
  file_size: number;
  message: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category?: string;
  sections?: string[];
  prompt?: string;
  output_format?: string;
  is_builtin: boolean;
}

export interface MeetingDetail {
  id: number;
  title: string;
  status: string;
  progress: number;
  video_path: string;
  duration?: number;
  one_line_summary?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  results?: Array<{
    id: number;
    transcript_raw?: string;
    transcript_enhanced?: string;
    summary_json?: any;
    llm_provider?: string;
    llm_model?: string;
  }>;
  summaries?: Array<{
    id: number;
    template_id: number;
    content: string;
    llm_provider?: string;
    llm_model?: string;
  }>;
}

/**
 * Upload meeting file with template selection
 * Note: Backend currently doesn't accept template_id in upload, it will be used later in summarize
 */
export async function uploadMeeting(
  file: File,
  title: string,
  templateId?: string
): Promise<ApiResponse<MeetingUploadResponse>> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    // Note: template_id will be passed later to summarize endpoint
    // Backend upload endpoint currently doesn't accept template_id

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      return { error: error.detail || 'Upload failed' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    // Check for common error types
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return { error: '无法连接后端服务，请确认后端已启动并允许跨域访问。当前前端运行在 http://localhost:5173，后端需要允许该源访问。' };
    }
    return { error: `Upload error: ${error}` };
  }
}

/**
 * Get all templates from backend
 */
export async function getTemplates(): Promise<ApiResponse<Template[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/templates`);

    if (!response.ok) {
      return { error: 'Failed to fetch templates' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: `Failed to fetch templates: ${error}` };
  }
}

/**
 * Get meeting history
 */
export async function getMeetingHistory(): Promise<ApiResponse<MeetingDetail[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/history`);

    if (!response.ok) {
      return { error: 'Failed to fetch meeting history' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: `Failed to fetch history: ${error}` };
  }
}

/**
 * Get meeting detail by ID
 */
export async function getMeetingDetail(meetingId: string): Promise<ApiResponse<MeetingDetail>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}`);

    if (!response.ok) {
      return { error: 'Meeting not found' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: `Failed to fetch meeting: ${error}` };
  }
}

/**
 * Get transcription status (note: backend uses /transcription-status not /status)
 */
export async function getMeetingStatus(meetingId: string): Promise<ApiResponse<{ status: string; progress: number }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}/transcription-status`);

    if (!response.ok) {
      return { error: 'Failed to fetch status' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: `Failed to fetch status: ${error}` };
  }
}

/**
 * Start transcription for a meeting
 */
export async function startTranscription(meetingId: string): Promise<ApiResponse<{ message: string }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}/transcribe`, {
      method: 'POST',
    });

    if (!response.ok) {
      return { error: 'Failed to start transcription' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: `Transcription error: ${error}` };
  }
}

/**
 * Generate summary for a meeting using specified template
 */
export async function generateSummary(
  meetingId: string,
  templateId: string
): Promise<ApiResponse<{ message: string; summary_id?: string }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}/summarize?template_id=${templateId}`, {
      method: 'POST',
    });

    if (!response.ok) {
      return { error: 'Failed to generate summary' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: `Summary generation error: ${error}` };
  }
}

/**
 * Delete a meeting
 */
export async function deleteMeeting(meetingId: number): Promise<ApiResponse<{ message: string }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      return { error: 'Failed to delete meeting' };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: `Delete error: ${error}` };
  }
}

/**
 * Poll meeting status until completion or failure
 */
export async function pollMeetingStatus(
  meetingId: string,
  onUpdate: (status: string, progress: number) => void,
  intervalMs: number = 2000
): Promise<{ status: string; progress: number }> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const result = await getMeetingStatus(meetingId);

        if (result.error) {
          reject(new Error(result.error));
          return;
        }

        const { status, progress } = result.data!;
        onUpdate(status, progress);

        // Stop polling if completed or failed
        if (status === 'completed' || status === 'failed') {
          resolve(result.data!);
          return;
        }

        // Continue polling
        setTimeout(poll, intervalMs);
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
}
