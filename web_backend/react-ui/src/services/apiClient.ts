/**
 * API Client
 * =========
 * 统一的API客户端，处理与后端的所有通信
 * 包含完整的错误处理、超时控制和fallback逻辑
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const API_TIMEOUT_MS = 120000; // 2分钟超时
// 阶段 10B-5-Q3：可配置的上传超时（默认10分钟，适合长音频）
const UPLOAD_TIMEOUT_MS = parseInt(import.meta.env.VITE_UPLOAD_TIMEOUT_MS || '600000'); // 默认10分钟

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ApiClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private uploadTimeout: number;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.defaultTimeout = API_TIMEOUT_MS;
    this.uploadTimeout = UPLOAD_TIMEOUT_MS;
  }

  /**
   * 创建带超时的AbortController
   */
  private createTimeoutController(timeoutMs: number): AbortController {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), timeoutMs);
    return controller;
  }

  /**
   * 通用请求方法
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = this.defaultTimeout
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = this.createTimeoutController(timeoutMs);

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      signal: controller.signal as AbortSignal,
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });

      // 检查是否是超时错误
      if (controller.signal.aborted) {
        return {
          success: false,
          error: `请求超时 (${timeoutMs / 1000}秒)，请稍后重试`,
        };
      }

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.message || data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data: data.data !== undefined ? data.data : data,
        message: data.message,
      };
    } catch (error) {
      // 检查是否是超时错误
      if (controller.signal.aborted) {
        return {
          success: false,
          error: `请求超时 (${timeoutMs / 1000}秒)，请稍后重试`,
        };
      }

      // 网络错误
      if (error instanceof TypeError && error.message.includes('fetch')) {
        return {
          success: false,
          error: '后端服务不可用，请检查后端是否启动',
        };
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : '网络错误，请稍后重试',
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async postFile<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = this.createTimeoutController(this.uploadTimeout);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal as AbortSignal,
      });

      // 检查是否是超时错误
      if (controller.signal.aborted) {
        return {
          success: false,
          error: `上传超时 (${this.uploadTimeout / 1000}秒)，请尝试：\n1. 上传更短的音频文件\n2. 稍后重试\n3. 或使用分段处理功能（开发中）`,
        };
      }

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.message || data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data: data.data !== undefined ? data.data : data,
        message: data.message,
      };
    } catch (error) {
      // 检查是否是超时错误
      if (controller.signal.aborted) {
        return {
          success: false,
          error: `上传超时 (${this.uploadTimeout / 1000}秒)，请尝试：\n1. 上传更短的音频文件\n2. 稍后重试\n3. 或使用分段处理功能（开发中）`,
        };
      }

      // 网络错误
      if (error instanceof TypeError && error.message.includes('fetch')) {
        return {
          success: false,
          error: '后端服务不可用，请检查后端是否启动',
        };
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : '上传失败，请稍后重试',
      };
    }
  }

  async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  /**
   * 检查后端是否可用
   */
  async checkHealth(): Promise<boolean> {
    try {
      const result = await this.get('/v1/health');
      return result.success;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export types
export type { ApiResponse };
