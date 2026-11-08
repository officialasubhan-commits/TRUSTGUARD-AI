export interface UrlValidationResult {
  isValid: boolean;
  normalizedUrl: string;
  error?: string;
}

export function validateAndNormalizeUrl(rawInput: string): UrlValidationResult {
  const trimmed = rawInput.trim();
  if (!trimmed) {
    return {
      isValid: false,
      normalizedUrl: '',
      error: 'Please enter a website URL.',
    };
  }

  // Auto-prepend https:// if no scheme is specified
  let target = trimmed;
  if (!/^https?:\/\//i.test(target)) {
    target = `https://${target}`;
  }

  try {
    const parsed = new URL(target);

    // Enforce scheme
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return {
        isValid: false,
        normalizedUrl: target,
        error: 'Only HTTP and HTTPS protocols are supported for security analysis.',
      };
    }

    const hostname = parsed.hostname.toLowerCase();

    // Pre-flight SSRF protection checks
    if (
      hostname === 'localhost' ||
      hostname.endsWith('.localhost') ||
      hostname === '127.0.0.1' ||
      hostname === '::1' ||
      hostname === '0.0.0.0' ||
      hostname.startsWith('127.') ||
      hostname.startsWith('10.') ||
      hostname.startsWith('192.168.') ||
      hostname === '169.254.169.254'
    ) {
      return {
        isValid: false,
        normalizedUrl: target,
        error: 'Security Boundary: Localhost, private networks, and cloud metadata IPs cannot be scanned.',
      };
    }

    if (!hostname.includes('.')) {
      return {
        isValid: false,
        normalizedUrl: target,
        error: 'Target domain must contain a valid top-level domain (e.g. .com, .org, .io).',
      };
    }

    return {
      isValid: true,
      normalizedUrl: parsed.toString(),
    };
  } catch {
    return {
      isValid: false,
      normalizedUrl: target,
      error: 'Malformed URL syntax. Please enter a valid web address.',
    };
  }
}

