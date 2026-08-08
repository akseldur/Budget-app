// Fargetokens hentet direkte fra ui-mockup.html sine CSS-variabler, slik at
// appen matcher den godkjente mockupen i stedet for å finne på et nytt uttrykk.

export const lightColors = {
  bg: '#eef1f3',
  page: '#f4f6f8',
  surface: '#ffffff',
  surface2: '#f7f9fa',
  ink: '#12161c',
  inkSoft: '#5c6672',
  inkFaint: '#939ca6',
  line: '#e6e9ed',
  accent: '#1f6f64',
  accentStrong: '#144a43',
  accentWash: '#e2f0ed',
  good: '#2f7d4f',
  goodWash: '#e4f2e8',
  warn: '#9c6d15',
  warnWash: '#f8eed9',
  critical: '#c6433d',
  criticalWash: '#fbe6e5',
};

export const darkColors = {
  bg: '#0d1013',
  page: '#14181d',
  surface: '#1a1f25',
  surface2: '#20262d',
  ink: '#eef1f3',
  inkSoft: '#a7b0ba',
  inkFaint: '#6d7680',
  line: '#2a3138',
  accent: '#6fc7b8',
  accentStrong: '#a9e0d5',
  accentWash: '#17332f',
  good: '#7fd39f',
  goodWash: '#163524',
  warn: '#e8c579',
  warnWash: '#3a2f14',
  critical: '#f0a09c',
  criticalWash: '#3a1a18',
};

export type ThemeColors = typeof lightColors;

export type BudgetStatus = 'green' | 'yellow' | 'red';

export function statusColor(colors: ThemeColors, status: BudgetStatus) {
  switch (status) {
    case 'green':
      return { dot: colors.good, wash: colors.goodWash, text: colors.good };
    case 'yellow':
      return { dot: colors.warn, wash: colors.warnWash, text: colors.warn };
    case 'red':
      return { dot: colors.critical, wash: colors.criticalWash, text: colors.critical };
  }
}

export const radius = { card: 18, pill: 20, sm: 10, md: 14 };
export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 };
