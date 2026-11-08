export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch {
    return dateString;
  }
}

export function formatTrustScore(score?: number | null): string {
  if (score === undefined || score === null || isNaN(score)) return '--';
  return Math.round(score).toString();
}

export function getRiskLevelFromScore(score: number): 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' {
  if (score < 25) return 'CRITICAL';
  if (score < 50) return 'HIGH';
  if (score < 75) return 'MEDIUM';
  return 'LOW';
}

