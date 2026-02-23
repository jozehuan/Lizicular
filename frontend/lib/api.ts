"use client";

import { useAuth } from "@/lib/auth-context";
import { useCallback, useMemo } from "react";

let refreshTokenPromise: Promise<string | null> | null = null;
const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const SAFE_METHODS = ["GET", "HEAD", "OPTIONS", "TRACE"];

function getCookie(name: string): string | null {
    if (typeof document === 'undefined') return null;
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
}

async function apiFetch(
  url: string,
  options: RequestInit = {},
  auth: {
    getAccessToken: () => string | null;
    refreshToken: () => Promise<boolean>;
    logout: () => Promise<void>;
  }
): Promise<Response> {
  const { getAccessToken, refreshToken, logout } = auth;

  const getHeaders = (accessToken: string | null): HeadersInit => {
    const headers: HeadersInit = {
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    };
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const method = options.method?.toUpperCase() || "GET";
    if (!SAFE_METHODS.includes(method)) {
        const csrfToken = getCookie("csrftoken");
        if (csrfToken) {
            headers["X-CSRF-Token"] = csrfToken;
        } else {
            console.warn("CSRF token not found for unsafe method request.");
        }
    }

    return headers;
  };

  const initialAccessToken = getAccessToken();
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(initialAccessToken),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    if (!refreshTokenPromise) {
      refreshTokenPromise = new Promise(async (resolve, reject) => {
        try {
          const success = await refreshToken();
          if (success) {
            resolve(getAccessToken());
          } else {
            await logout();
            reject(new Error("La sesión ha expirado. Por favor, inicia sesión de nuevo."));
          }
        } catch (e) {
          reject(e);
        } finally {
          refreshTokenPromise = null;
        }
      });
    }

    try {
      const newAccessToken = await refreshTokenPromise;
      if (newAccessToken) {
        // Retry with new CSRF token if it was rotated
        const retryHeaders = getHeaders(newAccessToken);
        return fetch(url, {
          ...options,
          headers: {
            ...retryHeaders,
            ...options.headers,
          },
        });
      } else {
        throw new Error("No se pudo refrescar la sesión.");
      }
    } catch (error) {
      throw error;
    }
  }

  return response;
}

export const useApi = () => {
  const { accessToken, refreshToken, logout } = useAuth();

  const wrappedFetch = useCallback(
    (path: string, options?: RequestInit) => {
      const getAccessToken = () => accessToken;
      const authUtils = { getAccessToken, refreshToken, logout };
      const fullUrl = `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
      return apiFetch(fullUrl, options, authUtils);
    },
    [accessToken, refreshToken, logout]
  );

  const api = useMemo(() => {
    const handleResponse = async <T>(response: Response): Promise<T> => {
      if (!response.ok) {
        const errorText = await response.text();
        try {
          // Try to parse the error text as JSON, which is the expected format for FastAPI errors
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        } catch (e) {
          // If parsing fails, it means we got a non-JSON response (e.g., HTML for a 404)
          // Throw a more informative error including the raw response body.
          throw new Error(`API Error: ${response.status} ${response.statusText}. Response: ${errorText.substring(0, 500)}`);
        }
      }
      // Handle successful responses
      const text = await response.text();
      return text ? JSON.parse(text) : ({} as T);
    };
  
    return {
      get: async <T>(url: string): Promise<T> => {
        const response = await wrappedFetch(url, { method: "GET" });
        return handleResponse<T>(response);
      },
      post: async <T>(url: string, body: any): Promise<T> => {
        const response = await wrappedFetch(url, {
          method: "POST",
          body: JSON.stringify(body),
        });
        return handleResponse<T>(response);
      },
      put: async <T>(url: string, body: any): Promise<T> => {
        const response = await wrappedFetch(url, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        return handleResponse<T>(response);
      },
      patch: async <T>(url: string, body: any): Promise<T> => {
        const response = await wrappedFetch(url, {
          method: 'PATCH',
          body: JSON.stringify(body),
        });
        return handleResponse<T>(response);
      },
      delete: async <T>(url: string): Promise<T> => {
        const response = await wrappedFetch(url, { method: "DELETE" });
        return handleResponse<T>(response);
      },
      postFormData: async <T>(url: string, formData: FormData): Promise<T> => {
        const response = await wrappedFetch(url, {
          method: "POST",
          body: formData,
        });
        return handleResponse<T>(response);
      },
      download: async (url: string): Promise<{ blob: Blob, filename: string }> => {
        const response = await wrappedFetch(url, { method: "GET" });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const contentDisposition = response.headers.get("Content-Disposition");
        let filename = "download";
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1];
          }
        }
        
        const blob = await response.blob();
        return { blob, filename };
      },
    };
  }, [wrappedFetch]);

  return api;
};

