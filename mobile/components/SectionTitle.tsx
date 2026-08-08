import { StyleSheet, Text } from 'react-native';

import { useTheme } from '@/constants/useTheme';

export function SectionTitle({ children }: { children: string }) {
  const colors = useTheme();
  return <Text style={[styles.text, { color: colors.inkFaint }]}>{children}</Text>;
}

const styles = StyleSheet.create({
  text: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    marginTop: 4,
    marginBottom: -2,
    marginLeft: 2,
  },
});
