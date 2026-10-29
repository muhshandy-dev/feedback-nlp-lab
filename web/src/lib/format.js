export const LABEL_ID = { negative: 'Negatif', neutral: 'Netral', positive: 'Positif' };

const nf = (d) => new Intl.NumberFormat('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d });
export const dec = (x, d = 3) => (x === null || x === undefined ? '-' : nf(d).format(x));
export const pct = (x, d = 1) => `${nf(d).format(x * 100)}%`;
export const int = (x) => new Intl.NumberFormat('id-ID').format(x);
export const ci = ([lo, hi], d = 3) => `${dec(lo, d)} sampai ${dec(hi, d)}`;

export function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function palette() {
  return {
    negative: cssVar('--neg'),
    neutral: cssVar('--neu'),
    positive: cssVar('--pos'),
    ink: cssVar('--ink'),
    muted: cssVar('--muted'),
    line: cssVar('--line'),
    grid: cssVar('--grid'),
    surface: cssVar('--surface'),
    negSoft: cssVar('--neg-soft'),
    posSoft: cssVar('--pos-soft'),
  };
}
