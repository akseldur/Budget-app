import { StyleSheet, View } from 'react-native';

import { BudgetStatus, statusColor } from '@/constants/theme';
import { useTheme } from '@/constants/useTheme';

export function Track({ status, fraction }: { status: BudgetStatus; fraction: number }) {
  const colors = useTheme();
  const { dot } = statusColor(colors, status);
  const width = `${Math.min(100, Math.max(0, fraction * 100))}%` as const;
  return (
    <View style={[styles.track, { backgroundColor: colors.surface2 }]}>
      <View style={[styles.fill, { width, backgroundColor: dot }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: { height: 8, borderRadius: 5, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: 5 },
});
