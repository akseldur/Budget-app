import { PropsWithChildren, ReactNode } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useTheme } from '@/constants/useTheme';

export function Screen({
  children,
  eyebrow,
  title,
  titleRight,
  onRefresh,
  refreshing,
}: PropsWithChildren<{
  eyebrow?: string;
  title: string;
  titleRight?: ReactNode;
  onRefresh?: () => void;
  refreshing?: boolean;
}>) {
  const colors = useTheme();
  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.page }]} edges={['top']}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          {eyebrow ? <Text style={[styles.eyebrow, { color: colors.inkFaint }]}>{eyebrow}</Text> : null}
          <Text style={[styles.title, { color: colors.ink }]}>{title}</Text>
        </View>
        {titleRight}
      </View>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        refreshControl={
          onRefresh ? (
            <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh} tintColor={colors.accent} />
          ) : undefined
        }
      >
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 20, paddingTop: 8, paddingBottom: 10 },
  eyebrow: { fontSize: 12, marginBottom: 2 },
  title: { fontSize: 24, fontWeight: '700', letterSpacing: -0.3 },
  scroll: { paddingHorizontal: 16, paddingBottom: 40, gap: 14 },
});
