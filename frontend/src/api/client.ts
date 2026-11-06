import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

export const API_BASE_URL: string =
  (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  statusCode?: number;
  data?: any;

  constructor(message: string, statusCode?: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.data = data;
  }
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message =
      (error.response?.data as any)?.detail ||
      (error.response?.data as any)?.message ||
      error.message ||
      'An unexpected error occurred';
    const statusCode = error.response?.status;
    const err = new ApiError(message, statusCode, error.response?.data);
    return Promise.reject(err);
  }
);

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.request<T>(config);
  return response.data;
}
