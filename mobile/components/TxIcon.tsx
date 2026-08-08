import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/constants/useTheme';

export function TxIcon({
  label,
  tone = 'accent',
  size = 36,
}: {
  label: string;
  tone?: 'accent' | 'neutral' | 'warn' | 'solid';
  size?: number;
}) {
  const colors = useTheme();
  const bg = { accent: colors.accentWash, neutral: colors.surface2, warn: colors.warnWash, solid: colors.accentStrong }[
    tone
  ];
  const fg = { accent: colors.accentStrong, neutral: colors.inkFaint, warn: colors.warn, solid: '#fff' }[tone];

  return (
    <View
      style={[
        styles.icon,
        { width: size, height: size, borderRadius: size * 0.28, backgroundColor: bg },
      ]}
    >
      <Text style={[styles.label, { color: fg, fontSize: size * 0.42 }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  icon: { alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  label: { fontWeight: '700' },
});
