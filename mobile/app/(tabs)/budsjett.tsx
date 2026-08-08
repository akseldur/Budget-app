import { useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { SectionTitle } from '@/components/SectionTitle';
import { StatusDot } from '@/components/StatusDot';
import { useTheme } from '@/constants/useTheme';
import { api, CategoryForecast } from '@/lib/api';
import { currentMonthStart, formatKr, formatMonthYear, shiftMonth } from '@/lib/format';
import { useAsync } from '@/lib/useAsync';

async function loadData(month: string) {
  const [status, categories] = await Promise.all([api.budget.status(month), api.categories.list()]);
  return { status, categories };
}

export default function BudsjettScreen() {
  const colors = useTheme();
  const [month, setMonth] = useState(currentMonthStart());
  const { data, loading, refreshing, refresh } = useAsync(() => loadData(month), [month]);

  const grouped = useMemo(() => {
    const categories = data?.categories ?? [];
    const byParent = new Map<string, CategoryForecast[]>();
    for (const line of data?.status ?? []) {
      const category = categories.find((c) => c.id === line.category_id);
      const parentId = category?.parent_id;
      const parentName = parentId ? categories.find((c) => c.id === parentId)?.name : undefined;
      const key = parentName ?? category?.name ?? 'Annet';
      if (!byParent.has(key)) byParent.set(key, []);
      byParent.get(key)!.push(line);
    }
    return Array.from(byParent.entries());
  }, [data]);

  return (
    <Screen
      title="Budsjett"
      titleRight={
        <View style={styles.monthSwitch}>
          <TouchableOpacity onPress={() => setMonth(shiftMonth(month, -1))} hitSlop={10}>
            <Text style={[styles.chevron, { color: colors.inkFaint }]}>‹</Text>
          </TouchableOpacity>
          <Text style={[styles.current, { color: colors.ink }]}>{formatMonthYear(month)}</Text>
          <TouchableOpacity onPress={() => setMonth(shiftMonth(month, 1))} hitSlop={10}>
            <Text style={[styles.chevron, { color: colors.inkFaint }]}>›</Text>
          </TouchableOpacity>
        </View>
      }
      onRefresh={refresh}
      refreshing={refreshing}
    >
      {loading && !data && <ActivityIndicator style={{ marginTop: 40 }} color={colors.accent} />}

      {data && grouped.length === 0 && (
        <Text style={{ color: colors.inkFaint, textAlign: 'center', marginTop: 30 }}>
          Ingen budsjettlinjer satt opp for {formatMonthYear(month).toLowerCase()} ennå.
        </Text>
      )}

      {grouped.map(([parentName, lines]) => (
        <View key={parentName}>
          <SectionTitle>{parentName}</SectionTitle>
          <Card style={{ padding: 4 }}>
            {lines.map((line) => (
              <View key={line.category_id} style={[styles.row, { borderBottomColor: colors.line }]}>
                <StatusDot status={line.status} />
                <Text style={[styles.name, { color: colors.ink }]}>{line.category_name}</Text>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text
                    style={[
                      styles.spent,
                      { color: line.spent_so_far > line.planned_amount ? colors.critical : colors.ink },
                    ]}
                  >
                    {formatKr(line.spent_so_far)}
                  </Text>
                  <Text style={[styles.planned, { color: colors.inkFaint }]}>av {formatKr(line.planned_amount)}</Text>
                </View>
              </View>
            ))}
          </Card>
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  monthSwitch: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingBottom: 6 },
  chevron: { fontSize: 18, paddingHorizontal: 4 },
  current: { fontSize: 13, fontWeight: '600' },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 11,
    paddingHorizontal: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  name: { flex: 1, fontSize: 14, fontWeight: '500' },
  spent: { fontSize: 14, fontWeight: '600' },
  planned: { fontSize: 11, marginTop: 1 },
});
