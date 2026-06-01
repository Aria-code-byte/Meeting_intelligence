/**
 * Transcription Service
 * 提供音频转文字的统一接口
 *
 * 阶段 10B-5-Q4：支持异步任务模式
 *
 * 当前支持：
 * - 异步任务模式（优先）：/api/v1/transcriptions/jobs
 * - 同步API调用（fallback）：/api/v1/transcribe
 * - WhisperX + pyannote 说话人分离（阶段 10B-4）
 * - 本地fallback模式（后端不可用时）
 */

import type { Meeting, TranscriptTurn } from '../types/models';
import { apiClient } from './apiClient';

export type TranscriptionProvider = 'fallback' | 'backend' | 'manual' | 'whisperx';

// 阶段 10B-5-Q4：异步任务状态类型
export type JobStatus = 'queued' | 'preprocessing' | 'transcribing' | 'aligning' | 'diarizing' | 'building_turns' | 'completed' | 'failed' | 'cancelled';

export interface TranscriptionInput {
  meetingId: string;
  file?: File;
  audioFileName?: string;
  // 阶段 10B-5-Q4：新增进度回调
  onProgress?: (stage: string, progress: number, message: string) => void;
}

// 阶段 10B-5-Q4：异步任务响应类型
interface CreateJobResponse {
  success: boolean;
  jobId?: string;
  status?: string;
  error?: string;
}

interface JobStatusResponse {
  success: boolean;
  jobId?: string;
  status?: JobStatus;
  stage?: string;
  progress?: number;
  message?: string;
  result?: {
    transcript: string;
    transcriptTurns?: TranscriptTurn[];
    audioDuration?: number;
    language?: string;
    transcriptionProvider: string;
    transcriptionModel?: string;
    diarizationEnabled?: boolean;
    diarizationProvider?: string;
    diarizationModel?: string;
    alignmentStatus?: 'success' | 'skipped' | 'failed';
    alignmentError?: string;
  };
  error?: string;
  timings?: {
    audioPreprocessTime: number;
    whisperTranscribeTime: number;
    alignTime: number;
    diarizationTime: number;
    buildTurnsTime: number;
    totalTime: number;
  };
}

/**
 * 阶段 10B-4：扩展 TranscriptionResult 支持 speaker turns
 */
export interface TranscriptionResult {
  transcript: string;
  // 阶段 10B-4：新增 transcriptTurns
  transcriptTurns?: TranscriptTurn[];
  provider: TranscriptionProvider;
  isFallback: boolean;
  processingTime?: number;
  error?: string;
  // 阶段 10B-4：新增 provider metadata 字段
  transcriptionModel?: string;
  diarizationEnabled?: boolean;
  diarizationProvider?: string;
  diarizationModel?: string;
  alignmentStatus?: 'success' | 'skipped' | 'failed';
  alignmentError?: string;
  // 阶段 10B-5-Q4：新增 audioDuration
  audioDuration?: number;
}

/**
 * 阶段 10B-5-Q4：异步转录会议音频（使用 job + polling）
 */
async function transcribeMeetingAudioAsync(
  file: File,
  audioFileName: string,
  onProgress?: (stage: string, progress: number, message: string) => void
): Promise<TranscriptionResult> {
  console.log('[TranscriptionService] 开始异步转录:', {
    fileName: audioFileName,
    fileSize: file.size,
  });

  try {
    // 1. 创建异步任务
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_size', 'base');
    formData.append('language', 'zh');

    onProgress?.('正在上传文件', 5, '正在上传音频文件...');

    const createResponse = await apiClient.postFile<CreateJobResponse>('/v1/transcriptions/jobs', formData);

    if (!createResponse.success || !createResponse.data?.jobId) {
      throw new Error(createResponse.error || '创建转录任务失败');
    }

    const jobId = createResponse.data.jobId;
    console.log('[TranscriptionService] 任务已创建:', jobId);

    onProgress?.('任务已创建', 10, '转录任务已创建，正在处理...');

    // 2. 轮询任务状态
    const pollingInterval = 2000; // 2秒
    // 根据文件大小动态调整超时时间：小文件 30 分钟，大文件最长 120 分钟
    const fileSizeMB = file.size / (1024 * 1024);
    const maxPollingTime = fileSizeMB > 500 ? 120 * 60 * 1000 :
                          fileSizeMB > 100 ? 90 * 60 * 1000 :
                          30 * 60 * 1000; // 小文件保持 30 分钟
    const startTime = Date.now();

    // 阶段 10B-5-Q5：减少日志刷屏，只在状态变化时打印
    let lastStatus: string | undefined = undefined;
    let lastProgress: number | undefined = undefined;
    let lastStage: string | undefined = undefined;

    while (Date.now() - startTime < maxPollingTime) {
      // 等待一段时间再轮询
      await new Promise(resolve => setTimeout(resolve, pollingInterval));

      // 查询任务状态
      const statusResponse = await apiClient.get<JobStatusResponse>(`/v1/transcriptions/jobs/${jobId}`);

      if (!statusResponse.success || !statusResponse.data) {
        throw new Error(statusResponse.error || '查询任务状态失败');
      }

      const jobData = statusResponse.data;

      // 阶段 10B-5-Q5：只在状态变化时打印日志
      const statusChanged = jobData.status !== lastStatus;
      const progressChanged = jobData.progress !== lastProgress;
      const stageChanged = jobData.stage !== lastStage;

      if (statusChanged || progressChanged || stageChanged) {
        console.log('[TranscriptionService] 任务状态变化:', {
          status: jobData.status,
          stage: jobData.stage,
          progress: jobData.progress,
          message: jobData.message,
        });
        lastStatus = jobData.status;
        lastProgress = jobData.progress;
        lastStage = jobData.stage;
      }

      // 更新进度
      onProgress?.(
        jobData.stage || '正在处理',
        jobData.progress || 0,
        jobData.message || ''
      );

      // 检查任务是否完成
      if (jobData.status === 'completed' && jobData.result) {
        console.log('[TranscriptionService] 转录成功');

        // 检查结果有效性
        const hasValidTranscript = jobData.result.transcript && jobData.result.transcript.trim().length > 0;
        const hasValidTurns = jobData.result.transcriptTurns && jobData.result.transcriptTurns.length > 0;

        if (!hasValidTranscript && !hasValidTurns) {
          throw new Error('转录完成但未返回有效内容');
        }

        return {
          transcript: jobData.result.transcript || '',
          transcriptTurns: jobData.result.transcriptTurns,
          provider: 'whisperx',
          isFallback: false,
          processingTime: jobData.timings?.totalTime,
          transcriptionModel: jobData.result.transcriptionModel,
          diarizationEnabled: jobData.result.diarizationEnabled,
          diarizationProvider: jobData.result.diarizationProvider,
          diarizationModel: jobData.result.diarizationModel,
          alignmentStatus: jobData.result.alignmentStatus,
          alignmentError: jobData.result.alignmentError,
          audioDuration: jobData.result.audioDuration,
        };
      }

      // 检查任务是否失败
      if (jobData.status === 'failed') {
        throw new Error(jobData.error || '转录任务失败');
      }

      // 检查任务是否取消
      if (jobData.status === 'cancelled') {
        throw new Error('用户已取消处理');
      }
    }

    // 超时
    const timeoutMinutes = Math.round(maxPollingTime / (60 * 1000));
    throw new Error(`转录任务处理超时（${timeoutMinutes}分钟）`);

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '异步转录失败';
    console.warn('[TranscriptionService] 异步转录失败:', errorMessage);

    return {
      transcript: '',
      provider: 'fallback',
      isFallback: true,
      error: `转录失败：${errorMessage}。请重试或手动粘贴会议文字稿`
    };
  }
}

/**
 * 同步转录会议音频（fallback 模式）
 */
async function transcribeMeetingAudioSync(input: TranscriptionInput): Promise<TranscriptionResult> {
  const { meetingId, file, audioFileName } = input;

  // 如果没有提供文件，直接返回 fallback 模式
  if (!file) {
    return {
      transcript: '',
      provider: 'fallback',
      isFallback: true,
      error: '请提供音频文件进行转录'
    };
  }

  try {
    console.log('[TranscriptionService] 开始同步转录:', {
      fileName: audioFileName,
      fileSize: file?.size,
    });

    // 创建 FormData 用于文件上传
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_size', 'base');
    formData.append('language', 'zh');

    // 调用后端 API: /api/v1/transcribe
    const response = await apiClient.postFile<{
      success: boolean;
      data?: {
        transcript: string;
        transcriptTurns?: TranscriptTurn[];
        segments?: Array<{ start: number; end: number; text: string }>;
        language?: string;
        transcriptionProvider: string;
        transcriptionModel?: string;
        diarizationEnabled?: boolean;
        diarizationProvider?: string;
        diarizationModel?: string;
        alignmentStatus?: 'success' | 'skipped' | 'failed';
        alignmentError?: string;
        audioDuration?: number;
      };
      provider: string;
      isFallback: boolean;
      processingTimeMs?: number;
      error?: string;
    }>('/v1/transcribe', formData);

    if (!response.success) {
      throw new Error(response.error || '转录请求失败');
    }

    const data = response.data;
    if (!data) {
      throw new Error('后端返回数据为空');
    }

    // 检查转录结果有效性
    const hasValidTranscript = data.transcript && data.transcript.trim().length > 0;
    const hasValidTurns = data.transcriptTurns && data.transcriptTurns.length > 0;

    if (!hasValidTranscript && !hasValidTurns) {
      console.error('[TranscriptionService] 后端返回成功但内容为空');
      throw new Error('后端转录接口返回成功，但未返回文字稿内容');
    }

    return {
      transcript: data.transcript || '',
      transcriptTurns: data.transcriptTurns,
      provider: (data.transcriptionProvider === 'whisperx' ? 'whisperx' :
                data.transcriptionProvider === 'backend' ? 'backend' : 'fallback'),
      isFallback: response.isFallback,
      processingTime: response.processingTimeMs,
      transcriptionModel: data.transcriptionModel,
      diarizationEnabled: data.diarizationEnabled,
      diarizationProvider: data.diarizationProvider,
      diarizationModel: data.diarizationModel,
      alignmentStatus: data.alignmentStatus,
      alignmentError: data.alignmentError,
      audioDuration: data.audioDuration,
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '转录服务暂不可用';
    console.warn('[TranscriptionService] 同步转录失败:', errorMessage);

    return {
      transcript: '',
      provider: 'fallback',
      isFallback: true,
      error: `转录失败：${errorMessage}。请重试或手动粘贴会议文字稿`
    };
  }
}

/**
 * 转录会议音频（统一接口）
 * 阶段 10B-5-Q4：优先使用异步任务模式
 */
export async function transcribeMeetingAudio(input: TranscriptionInput): Promise<TranscriptionResult> {
  const { file, audioFileName, onProgress } = input;

  if (!file) {
    return {
      transcript: '',
      provider: 'fallback',
      isFallback: true,
      error: '请提供音频文件进行转录'
    };
  }

  // 尝试使用异步模式
  try {
    return await transcribeMeetingAudioAsync(file, audioFileName || file.name, onProgress);
  } catch (error) {
    // 异步模式失败，回退到同步模式
    console.warn('[TranscriptionService] 异步模式失败，回退到同步模式:', error);
    return transcribeMeetingAudioSync(input);
  }
}

/**
 * 检查是否可以进行真实转录
 */
export async function canUseRealTranscription(): Promise<boolean> {
  try {
    const response = await apiClient.get<{
      status: string;
      transcriptionFallback: boolean;
    }>('/v1/health');

    return response.success && response.data?.transcriptionFallback === false;
  } catch {
    return false;
  }
}

/**
 * 获取转录服务状态描述
 */
export async function getTranscriptionServiceStatus(): Promise<{
  available: boolean;
  provider: TranscriptionProvider;
  description: string;
}> {
  try {
    const response = await apiClient.get<{
      transcription: {
        type: string;
        available: boolean;
      };
    }>('/v1/providers/info');

    if (response.success && response.data?.transcription) {
      const { type, available } = response.data.transcription;
      return {
        available,
        provider: type === 'backend' ? 'backend' : 'fallback',
        description: available
          ? `使用 ${type} 模式进行语音转录`
          : '后端转录服务暂不可用，使用本地 fallback 模式'
      };
    }
  } catch {
    // 忽略错误
  }

  return {
    available: false,
    provider: 'fallback',
    description: '后端服务不可用，使用本地 fallback 模式'
  };
}

/**
 * 标记文字稿为手动编辑
 */
export function markTranscriptAsManual(meeting: Meeting): Partial<Meeting> {
  return {
    transcriptionProvider: 'manual',
    transcriptionIsFallback: false,
    updatedAt: new Date().toISOString()
  };
}
