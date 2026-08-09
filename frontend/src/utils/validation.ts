/** Shared client-side validation utilities mirroring backend rules. */

const EMAIL_RE = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
const MACHINE_ID_RE = /^[A-Z0-9][A-Z0-9\-_]{2,31}$/i;
const SCRIPT_RE = /<script|javascript:|on\w+\s*=/i;

export type FieldErrors = Record<string, string>;

export function validateRequired(value: string, field: string, min = 1): string | null {
  const trimmed = value.trim();
  if (trimmed.length < min) return `${field} is required`;
  if (SCRIPT_RE.test(trimmed)) return `${field} contains disallowed content`;
  return null;
}

export function validateEmail(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return 'Email is required';
  if (!EMAIL_RE.test(trimmed)) return 'Invalid email address';
  return null;
}

export function validatePassword(value: string): string | null {
  if (!value) return 'Password is required';
  if (value.length < 6) return 'Password must be at least 6 characters';
  return null;
}

export function validateMachineId(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (!MACHINE_ID_RE.test(trimmed)) return 'Invalid machine ID format';
  return null;
}

export function validateLength(value: string, field: string, min: number, max: number): string | null {
  const trimmed = value.trim();
  if (trimmed.length < min) return `${field} must be at least ${min} characters`;
  if (trimmed.length > max) return `${field} must not exceed ${max} characters`;
  return null;
}

export function validateDueDate(value: string): string | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (isNaN(parsed.getTime())) return 'Invalid date format';
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (parsed < today) return 'Due date cannot be in the past';
  return null;
}

export function validateImageFile(file: File | null, maxMb = 10): string | null {
  if (!file) return 'Please select an image file';
  const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
  if (!allowed.includes(file.type)) return 'File must be JPEG, PNG, or WebP';
  if (file.size > maxMb * 1024 * 1024) return `File too large (max ${maxMb}MB)`;
  return null;
}

export function validateQuestion(value: string): string | null {
  const err = validateLength(value, 'Question', 5, 1000);
  if (err) return err;
  if (SCRIPT_RE.test(value)) return 'Question contains disallowed content';
  return null;
}

export function parseApiError(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as { response?: { data?: { error?: { message?: string; details?: { fields?: { message: string }[] } } } } }).response;
    const msg = resp?.data?.error?.message;
    const fields = resp?.data?.error?.details?.fields;
    if (fields?.length) return fields.map((f) => f.message).join('. ');
    if (msg) return msg;
  }
  if (error instanceof Error && error.message.includes('Network Error')) {
    return 'Network error. Check your connection and try again.';
  }
  return 'An unexpected error occurred. Please try again.';
}
