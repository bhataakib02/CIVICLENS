import { ApiErrorResponse } from '@/types/api';

export class ApiError extends Error {
  code: string;
  statusCode: number;
  requestId?: string;
  fieldErrors?: Array<{ field: string; message: string }>;

  constructor(statusCode: number, code: string, message: string, requestId?: string, fieldErrors?: Array<{ field: string; message: string }>) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.code = code;
    this.requestId = requestId;
    this.fieldErrors = fieldErrors;
  }
}

export class NetworkError extends Error {
  constructor(message = 'Network request failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export function normalizeApiError(statusCode: number, errorData: any): ApiError {
  const payload: ApiErrorResponse = errorData;
  if (payload && payload.error) {
    return new ApiError(
      statusCode,
      payload.error.code || 'UNKNOWN_ERROR',
      payload.error.message || 'An error occurred while processing your request.',
      payload.error.request_id,
      payload.error.field_errors
    );
  }

  const defaultMessages: Record<number, { code: string; message: string }> = {
    400: { code: 'BAD_REQUEST', message: 'The request was invalid.' },
    401: { code: 'UNAUTHORIZED', message: 'Authentication is required.' },
    403: { code: 'FORBIDDEN', message: 'You do not have permission to perform this action.' },
    404: { code: 'NOT_FOUND', message: 'The requested resource was not found.' },
    409: { code: 'CONFLICT', message: 'The operation conflicted with existing server state.' },
    422: { code: 'VALIDATION_ERROR', message: 'Validation failed.' },
    429: { code: 'RATE_LIMITED', message: 'Too many requests. Please try again later.' },
    500: { code: 'INTERNAL_ERROR', message: 'An internal server error occurred.' },
    503: { code: 'SERVICE_UNAVAILABLE', message: 'The service is temporarily unavailable.' }
  };

  const fallback = defaultMessages[statusCode] || { code: 'HTTP_ERROR', message: `HTTP error ${statusCode}` };
  return new ApiError(statusCode, fallback.code, fallback.message);
}
