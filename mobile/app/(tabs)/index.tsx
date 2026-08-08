import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useMemo } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Svg, { Polyline } from 'react-native-svg';

import { Card } from '@/components/Card';
import { Chip } from '@/components/Chip';
import { Screen } from '@/components/Screen';
import { SectionTitle } from '@/components/SectionTitle';
import { StatusDot } from '@/components/StatusDot';
import { Track } from '@/components/Track';
import { TxIcon } from '@/components/TxIcon';
import { useTheme } from '@/constants/useTheme';
import { BudgetStatus } from '@/constants/theme';
import { api, Account, CategoryForecast, Transaction } from '@/lib/api';
import { currentMonthStart, formatKr, initials } from '@/lib/format';
import { useAsync } from '@/lib/useAsync';

const STATUS_LABEL: Record<BudgetStatus, string> = { green: 'Grønn', yellow: 'Gul', red: 'Rød' };
const STATUS_RANK: Record<BudgetStatus, number> = { red: 0, yellow: 1, green: 2 };

interface OversiktData {
  accounts: (Account & { balance: number | null })[];
  fund: Awaited<ReturnType<typeof api.funds.dnbTeknologiA>> | null;
  categories: CategoryForecast[];
  transactions: Transaction[];
}

async function loadOversikt(): Promise<OversiktData> {
  const [accounts, fund, categories, transactions] = await Promise.all([
    api.accounts.list(),
    api.funds.dnbTeknologiA().catch(() => null),
    api.budget.status(currentMonthStart()).catch(() => []),
    api.transactions.list().catch(() => []),
  ]);

  const withBalances = await Promise.all(
    accounts.map(async (account) => {
      const balance = await api.accounts.balance(account.id).catch(() => null);
      return { ...account, balance: balance?.amount ?? null };
    }),
  );

  return { accounts: withBalances, fund, categories, transactions };
}

export default function OversiktScreen() {
  const colors = useTheme();
  const router = useRouter();
  const today = new Date().toLocaleDateString('nb-NO', { weekday: 'long', day: 'numeric', month: 'long' });
  const { data, loading, refreshing, refresh } = useAsync(loadOversikt, []);

  const totals = useMemo(() => {
    const cats = data?.categories ?? [];
    const spent = cats.reduce((sum, c) => sum + c.spent_so_far, 0);
    const planned = cats.reduce((sum, c) => sum + c.planned_amount, 0);
    const worst = cats.reduce<BudgetStatus>(
      (acc, c) => (STATUS_RANK[c.status] < STATUS_RANK[acc] ? c.status : acc),
      'green',
    );
    return { spent, planned, worst, fraction: planned > 0 ? spent / planned : 0 };
  }, [data]);

  const watchCategories = useMemo(
    () =>
      [...(data?.categories ?? [])]
        .sort((a, b) => STATUS_RANK[a.status] - STATUS_RANK[b.status])
        .slice(0, 3),
    [data],
  );

  const uncategorizedCount = useMemo(
    () => (data?.transactions ?? []).filter((t) => t.splits.some((s) => s.category_id === null)).length,
    [data],
  );

  const recentTransactions = (data?.transactions ?? []).slice(0, 5);

  if (loading && !data) {
    return (
      <Screen title="Oversikt">
        <ActivityIndicator style={{ marginTop: 40 }} color={colors.accent} />
      </Screen>
    );
  }

  return (
    <Screen
      title="Oversikt"
      eyebrow={today}
      onRefresh={refresh}
      refreshing={refreshing}
      titleRight={
        <View style={{ flexDirection: 'row', gap: 16, paddingBottom: 4 }}>
          <TouchableOpacity onPress={() => router.push('/kontoer')} hitSlop={8}>
            <Ionicons name="wallet-outline" size={22} color={colors.inkSoft} />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => router.push('/ny-transaksjon')} hitSlop={8}>
            <Ionicons name="add-circle-outline" size={22} color={colors.inkSoft} />
          </TouchableOpacity>
        </View>
      }
    >
      <View style={styles.balanceRow}>
        {(data?.accounts ?? []).slice(0, 2).map((account) => (
          <Card key={account.id} style={styles.balanceCard}>
            <Text style={[styles.label, { color: colors.inkFaint }]}>{account.bank_name}</Text>
            <Text style={[styles.amt, { color: colors.ink }]}>
              {account.balance !== null ? formatKr(account.balance) : '—'}
            </Text>
            <Text style={[styles.sub, { color: colors.inkFaint }]}>{account.currency}</Text>
          </Card>
        ))}
        {(data?.accounts?.length ?? 0) === 0 && (
          <TouchableOpacity style={{ flex: 1 }} onPress={() => router.push('/kontoer')}>
            <Card>
              <Text style={{ color: colors.accentStrong, fontWeight: '600' }}>Koble til en bankkonto →</Text>
            </Card>
          </TouchableOpacity>
        )}
      </View>

      {data?.fund && (
        <Card style={{ backgroundColor: colors.accentStrong }}>
          <Text style={[styles.label, { color: '#fff', opacity: 0.75 }]}>{data.fund.name}</Text>
          <View style={styles.fundRow}>
            <Text style={styles.fundPrice}>{formatKr(data.fund.price)}</Text>
          </View>
          <Svg width="100%" height={30} viewBox="0 0 280 34" style={{ marginTop: 8 }}>
            <Polyline
              points="0,26 30,24 60,27 90,20 120,22 150,14 180,17 210,10 240,12 280,4"
              fill="none"
              stroke="#9fe6c9"
              strokeWidth={2}
            />
          </Svg>
        </Card>
      )}

      {data && data.categories.length > 0 && (
        <Card>
          <View style={styles.summaryRow}>
            <Text style={{ color: colors.ink }}>
              <Text style={styles.summaryAmt}>{formatKr(totals.spent)} </Text>
              <Text style={{ color: colors.inkSoft }}>av {formatKr(totals.planned)}</Text>
            </Text>
            <Chip tone={totals.worst === 'green' ? 'accent' : 'neutral'}>{STATUS_LABEL[totals.worst]}</Chip>
          </View>
          <Track status={totals.worst} fraction={totals.fraction} />
        </Card>
      )}

      {uncategorizedCount > 0 && (
        <TouchableOpacity onPress={() => router.push('/kategoriser')}>
          <View style={[styles.nudge, { backgroundColor: colors.accentWash }]}>
            <View style={[styles.badge, { backgroundColor: colors.accentStrong }]}>
              <Text style={styles.badgeText}>{uncategorizedCount}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.nudgeTitle, { color: colors.accentStrong }]}>Ukategoriserte transaksjoner</Text>
              <Text style={[styles.nudgeSub, { color: colors.accentStrong }]}>
                Trykk for å sortere dem, tar under et minutt
              </Text>
            </View>
            <Text style={[styles.chevron, { color: colors.accentStrong }]}>›</Text>
          </View>
        </TouchableOpacity>
      )}

      {watchCategories.length > 0 && (
        <>
          <SectionTitle>Kategorier å følge med på</SectionTitle>
          <Card style={{ padding: 4 }}>
            {watchCategories.map((c) => (
              <View key={c.category_id} style={[styles.catRow, { borderBottomColor: colors.line }]}>
                <StatusDot status={c.status} />
                <View style={{ flex: 1 }}>
                  <Text style={[styles.catName, { color: colors.ink }]}>{c.category_name}</Text>
                  <Text style={[styles.catSub, { color: colors.inkFaint }]}>Prognose {formatKr(c.projected)}</Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={[styles.catSpent, { color: colors.ink }]}>{formatKr(c.spent_so_far)}</Text>
                  <Text style={[styles.catPlanned, { color: colors.inkFaint }]}>av {formatKr(c.planned_amount)}</Text>
                </View>
              </View>
            ))}
          </Card>
        </>
      )}

      {recentTransactions.length > 0 && (
        <>
          <SectionTitle>Siste transaksjoner</SectionTitle>
          <Card style={{ padding: 4 }}>
            {recentTransactions.map((t) => (
              <TouchableOpacity key={t.id} onPress={() => router.push(`/transaksjon/${t.id}`)}>
                <View style={[styles.txRow, { borderBottomColor: colors.line }]}>
                  <TxIcon label={initials(t.description)} tone={t.amount > 0 ? 'solid' : 'accent'} />
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.merchant, { color: colors.ink }]} numberOfLines={1}>
                      {t.description}
                    </Text>
                  </View>
                  <Text style={[styles.amt2, { color: t.amount > 0 ? colors.good : colors.ink }]}>
                    {formatKr(t.amount)}
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </Card>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  balanceRow: { flexDirection: 'row', gap: 10 },
  balanceCard: { flex: 1 },
  label: { fontSize: 12, marginBottom: 3 },
  amt: { fontSize: 20, fontWeight: '700' },
  sub: { fontSize: 11, marginTop: 2 },
  fundRow: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between' },
  fundPrice: { fontSize: 26, fontWeight: '700', color: '#fff' },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 },
  summaryAmt: { fontSize: 19, fontWeight: '700' },
  nudge: { flexDirection: 'row', alignItems: 'center', gap: 12, borderRadius: 16, padding: 14 },
  badge: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  badgeText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  nudgeTitle: { fontSize: 14, fontWeight: '600' },
  nudgeSub: { fontSize: 12, opacity: 0.8, marginTop: 1 },
  chevron: { fontSize: 20 },
  catRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 11,
    paddingHorizontal: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  catName: { fontSize: 14, fontWeight: '500' },
  catSub: { fontSize: 12, marginTop: 1 },
  catSpent: { fontSize: 14, fontWeight: '600' },
  catPlanned: { fontSize: 11, marginTop: 1 },
  txRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  merchant: { fontSize: 14, fontWeight: '500' },
  amt2: { fontSize: 14, fontWeight: '600' },
});
