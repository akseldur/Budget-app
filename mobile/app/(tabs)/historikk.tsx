import { useRouter } from 'expo-router';
import { useMemo } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { SectionTitle } from '@/components/SectionTitle';
import { BudgetStatus } from '@/constants/theme';
import { useTheme } from '@/constants/useTheme';
import { api } from '@/lib/api';
import { currentMonthStart, formatKr, formatMonthYear, shiftMonth } from '@/lib/format';
import { useAsync } from '@/lib/useAsync';

const STATUS_RANK: Record<BudgetStatus, number> = { red: 0, yellow: 1, green: 2 };
const MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Des'];

interface MonthSummary {
  month: string;
  spent: number;
  planned: number;
  status: BudgetStatus;
}

async function loadHistory(): Promise<MonthSummary[]> {
  const months = Array.from({ length: 6 }, (_, i) => shiftMonth(currentMonthStart(), -(5 - i)));
  const results = await Promise.all(
    months.map(async (month) => {
      const lines = await api.budget.status(month).catch(() => []);
      const spent = lines.reduce((sum, l) => sum + l.spent_so_far, 0);
      const planned = lines.reduce((sum, l) => sum + l.planned_amount, 0);
      const status = lines.reduce<BudgetStatus>(
        (acc, l) => (STATUS_RANK[l.status] < STATUS_RANK[acc] ? l.status : acc),
        'green',
      );
      return { month, spent, planned, status };
    }),
  );
  return results;
}

export default function HistorikkScreen() {
  const colors = useTheme();
  const router = useRouter();
  const { data, loading, refreshing, refresh } = useAsync(loadHistory, []);
  const thisMonth = currentMonthStart();

  const maxSpent = useMemo(() => Math.max(1, ...(data ?? []).map((m) => m.spent)), [data]);

  const statusColorFor = (status: BudgetStatus) =>
    status === 'red' ? colors.critical : status === 'yellow' ? colors.warn : colors.good;

  if (loading && !data) {
    return (
      <Screen title="Historikk">
        <ActivityIndicator style={{ marginTop: 40 }} color={colors.accent} />
      </Screen>
    );
  }

  return (
    <Screen title="Historikk" onRefresh={refresh} refreshing={refreshing}>
      <Card>
        <View style={styles.chart}>
          {(data ?? []).map((m) => {
            const [, monthNum] = m.month.split('-');
            const isCurrent = m.month === thisMonth;
            const height = Math.max(6, (m.spent / maxSpent) * 96);
            return (
              <View key={m.month} style={styles.barWrap}>
                <View
                  style={[
                    styles.bar,
                    {
                      height,
                      backgroundColor: statusColorFor(m.status),
                      outlineColor: isCurrent ? colors.accentStrong : undefined,
                    },
                    isCurrent && { borderWidth: 2, borderColor: colors.accentStrong },
                  ]}
                />
                <Text style={[styles.barLabel, { color: colors.inkFaint }]}>
                  {MONTH_ABBR[Number(monthNum) - 1]}
                </Text>
              </View>
            );
          })}
        </View>
      </Card>

      <SectionTitle>Måneder</SectionTitle>
      <Card style={{ padding: 4 }}>
        {(data ?? [])
          .slice()
          .reverse()
          .map((m) => {
            const isCurrent = m.month === thisMonth;
            return (
              <TouchableOpacity key={m.month} onPress={() => router.push('/(tabs)/budsjett')}>
                <View style={[styles.monthRow, { borderBottomColor: colors.line }]}>
                  <View style={{ flex: 1 }}>
                    <Text
                      style={[
                        styles.monthName,
                        { color: isCurrent ? colors.accentStrong : colors.ink, fontWeight: isCurrent ? '700' : '500' },
                      ]}
                    >
                      {formatMonthYear(m.month)}
                    </Text>
                    {isCurrent && <Text style={[styles.monthSub, { color: colors.inkFaint }]}>Så langt denne måneden</Text>}
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text
                      style={[styles.monthSpent, { color: m.spent > m.planned ? colors.critical : colors.ink }]}
                    >
                      {formatKr(m.spent)}
                    </Text>
                    <Text style={[styles.monthPlanned, { color: colors.inkFaint }]}>av {formatKr(m.planned)}</Text>
                  </View>
                  <Text style={[styles.chev, { color: colors.inkFaint }]}>›</Text>
                </View>
              </TouchableOpacity>
            );
          })}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  chart: { flexDirection: 'row', alignItems: 'flex-end', gap: 10, height: 110, paddingTop: 4 },
  barWrap: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', gap: 6, height: '100%' },
  bar: { width: '100%', maxWidth: 22, borderRadius: 5 },
  barLabel: { fontSize: 11, fontWeight: '600' },
  monthRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  monthName: { fontSize: 14 },
  monthSub: { fontSize: 11, marginTop: 1 },
  monthSpent: { fontSize: 14, fontWeight: '600' },
  monthPlanned: { fontSize: 11, marginTop: 1 },
  chev: { fontSize: 18 },
});
