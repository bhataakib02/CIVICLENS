export function formatCurrency(amount: number | null | undefined, locale = 'en-IN'): string {
  if (amount == null || isNaN(amount)) return 'N/A';
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount);
}
