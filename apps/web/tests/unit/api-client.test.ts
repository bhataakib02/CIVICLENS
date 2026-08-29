import { describe, it, expect } from 'vitest';
import { normalizeApiError, UnauthorizedError, ValidationError, RateLimitError } from '../../lib/api/errors';

describe('API Error Normalization', () => {
  it('normalizes 401 response into UnauthorizedError', () => {
    const err = normalizeApiError(401, { error: { code: 'UNAUTHORIZED', message: 'Token expired', request_id: 'req_1' } });
    expect(err).toBeInstanceOf(UnauthorizedError);
    expect(err.message).toBe('Token expired');
    expect(err.status).toBe(401);
  });

  it('normalizes 422 response with field errors into ValidationError', () => {
    const err = normalizeApiError(422, {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid phone',
        request_id: 'req_2',
        field_errors: [{ field: 'phone_number', message: 'Must be 10 digits' }]
      }
    });
    expect(err).toBeInstanceOf(ValidationError);
    expect(err.status).toBe(422);
    expect(err.fieldErrors?.length).toBe(1);
    expect(err.fieldErrors?.[0].field).toBe('phone_number');
  });

  it('normalizes 429 response into RateLimitError', () => {
    const err = normalizeApiError(429, { error: { code: 'RATE_LIMITED', message: 'Too many OTP requests', request_id: 'req_3' } });
    expect(err).toBeInstanceOf(RateLimitError);
    expect(err.status).toBe(429);
  });
});
