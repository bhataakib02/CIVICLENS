export class AppError extends Error {
  public code: string;
  public status: number;
  public fieldErrors?: Array<{ field: string; message: string }>;

  constructor(message: string, code = 'APP_ERROR', status = 500, fieldErrors?: Array<{ field: string; message: string }>) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Session expired or unauthorized. Please log in again.', code = 'UNAUTHORIZED') {
    super(message, code, 401);
    this.name = 'UnauthorizedError';
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'You do not have permission to access this resource.', code = 'FORBIDDEN') {
    super(message, code, 403);
    this.name = 'ForbiddenError';
  }
}

export class NotFoundError extends AppError {
  constructor(message = 'Requested resource not found.', code = 'NOT_FOUND') {
    super(message, code, 404);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends AppError {
  constructor(message = 'Validation failed for request parameters.', fieldErrors?: Array<{ field: string; message: string }>, code = 'VALIDATION_ERROR') {
    super(message, code, 422, fieldErrors);
    this.name = 'ValidationError';
  }
}

export class ConflictError extends AppError {
  constructor(message = 'A conflict occurred with existing resource state.', code = 'CONFLICT') {
    super(message, code, 409);
    this.name = 'ConflictError';
  }
}

export class RateLimitError extends AppError {
  constructor(message = 'Too many requests. Please wait a moment and try again.', code = 'RATE_LIMITED') {
    super(message, code, 429);
    this.name = 'RateLimitError';
  }
}

export class ServerError extends AppError {
  constructor(message = 'A server error occurred. Please try again later.', code = 'SERVER_ERROR') {
    super(message, code, 500);
    this.name = 'ServerError';
  }
}

export class NetworkError extends AppError {
  constructor(message = 'Network error. Please check your internet connection.', code = 'NETWORK_ERROR') {
    super(message, code, 0);
    this.name = 'NetworkError';
  }
}

export function normalizeApiError(status: number, data: any): AppError {
  const code = data?.error?.code || 'UNKNOWN_ERROR';
  const message = data?.error?.message || data?.detail || 'An unexpected error occurred.';
  const fieldErrors = data?.error?.field_errors;

  if (status === 401) return new UnauthorizedError(message, code);
  if (status === 403) return new ForbiddenError(message, code);
  if (status === 404) return new NotFoundError(message, code);
  if (status === 409) return new ConflictError(message, code);
  if (status === 422) return new ValidationError(message, fieldErrors, code);
  if (status === 429) return new RateLimitError(message, code);
  if (status >= 500) return new ServerError(message, code);

  return new AppError(message, code, status, fieldErrors);
}
