import { PropsWithChildren } from 'react';
import { StyleSheet, Text } from 'react-native';

import { useTheme } from '@/constants/useTheme';

export function Chip({
  children,
  tone = 'neutral',
}: PropsWithChildren<{ tone?: 'neutral' | 'accent' }>) {
  const colors = useTheme();
  const bg = tone === 'accent' ? colors.accentWash : colors.surface2;
  const fg = tone === 'accent' ? colors.accentStrong : colors.inkSoft;
  return (
    <Text style={[styles.chip, { backgroundColor: bg, color: fg }]} numberOfLines={1}>
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  chip: {
    fontSize: 11,
    fontWeight: '600',
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 20,
    overflow: 'hidden',
  },
});
