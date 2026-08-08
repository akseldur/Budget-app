import { StyleSheet, View } from 'react-native';

import { BudgetStatus, statusColor } from '@/constants/theme';
import { useTheme } from '@/constants/useTheme';

export function StatusDot({ status }: { status: BudgetStatus }) {
  const colors = useTheme();
  const { dot } = statusColor(colors, status);
  return <View style={[styles.dot, { backgroundColor: dot }]} />;
}

const styles = StyleSheet.create({
  dot: { width: 9, height: 9, borderRadius: 5, flexShrink: 0 },
});
