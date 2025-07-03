import { Config } from '../config';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public isTimeout: boolean = false) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ApiClient {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = Config.API_BASE_URL;
    this.timeout = Config.API_TIMEOUT;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    customTimeout?: number
  ): Promise<ApiResponse<T>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), customTimeout || this.timeout);

    try {
      const url = `${this.baseURL}${endpoint}`;
      
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new ApiError(response.status, `API Error: ${response.statusText}`);
      }

      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      return {
        data,
        status: response.status,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new ApiError(408, 'Request timed out - server is taking too long to respond', true);
      }
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(0, `Network error: ${error.message}`);
    }
  }

  // GET request
  async get<T>(endpoint: string, customTimeout?: number): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'GET' }, customTimeout);
  }

  // POST request
  async post<T>(endpoint: string, data?: any, customTimeout?: number): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      customTimeout
    );
  }

  // PUT request
  async put<T>(endpoint: string, data?: any, customTimeout?: number): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(
      endpoint,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      customTimeout
    );
  }

  // PATCH request
  async patch<T>(endpoint: string, data?: any, customTimeout?: number): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(
      endpoint,
      {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
      },
      customTimeout
    );
  }

  // DELETE request
  async delete<T>(endpoint: string, customTimeout?: number): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' }, customTimeout);
  }
}

// Export a singleton instance
export const apiClient = new ApiClient();