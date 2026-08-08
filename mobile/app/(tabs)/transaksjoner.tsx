import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { Card } from '@/components/Card';
import { Chip } from '@/components/Chip';
import { Screen } from '@/components/Screen';
import { TxIcon } from '@/components/TxIcon';
import { useTheme } from '@/constants/useTheme';
import { api, Category, Transaction } from '@/lib/api';
import { formatKr, initials } from '@/lib/format';
import { useAsync } from '@/lib/useAsync';

type Filter = 'alle' | 'ukategorisert' | 'splittet' | 'inntekt';

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'alle', label: 'Alle' },
  { key: 'ukategorisert', label: 'Ukategorisert' },
  { key: 'splittet', label: 'Splittet' },
  { key: 'inntekt', label: 'Inntekt' },
];

function categoryLabel(categories: Category[], categoryId: string | null): string {
  if (categoryId === null) return 'Ukategorisert';
  const category = categories.find((c) => c.id === categoryId);
  if (!category) return 'Ukategorisert';
  const parent = categories.find((c) => c.id === category.parent_id);
  return parent ? `${parent.name} / ${category.name}` : category.name;
}

async function loadData() {
  const [transactions, categories] = await Promise.all([api.transactions.list(), api.categories.list()]);
  return { transactions, categories };
}

export default function TransaksjonerScreen() {
  const colors = useTheme();
  const router = useRouter();
  const [filter, setFilter] = useState<Filter>('alle');
  const { data, loading, refreshing, refresh } = useAsync(loadData, []);

  const filtered = useMemo(() => {
    const all = data?.transactions ?? [];
    switch (filter) {
      case 'ukategorisert':
        return all.filter((t) => t.splits.some((s) => s.category_id === null));
      case 'splittet':
        return all.filter((t) => t.splits.length > 1);
      case 'inntekt':
        return all.filter((t) => t.amount > 0);
      default:
        return all;
    }
  }, [data, filter]);

  if (loading && !data) {
    return (
      <Screen title="Transaksjoner">
        <ActivityIndicator style={{ marginTop: 40 }} color={colors.accent} />
      </Screen>
    );
  }

  return (
    <Screen title="Transaksjoner" onRefresh={refresh} refreshing={refreshing}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow}>
        {FILTERS.map((f) => (
          <TouchableOpacity key={f.key} onPress={() => setFilter(f.key)}>
            <View
              style={[
                styles.pill,
                {
                  backgroundColor: filter === f.key ? colors.accentStrong : colors.surface2,
                  marginRight: 8,
                },
              ]}
            >
              <Text style={{ color: filter === f.key ? '#fff' : colors.inkSoft, fontWeight: '600', fontSize: 12 }}>
                {f.label}
              </Text>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Card style={{ padding: 4 }}>
        {filtered.length === 0 && (
          <Text style={{ color: colors.inkFaint, padding: 12, textAlign: 'center' }}>
            Ingen transaksjoner her ennå.
          </Text>
        )}
        {filtered.map((t) => (
          <TransactionRow
            key={t.id}
            transaction={t}
            categories={data?.categories ?? []}
            onPress={() => router.push(`/transaksjon/${t.id}`)}
          />
        ))}
      </Card>
    </Screen>
  );
}

function TransactionRow({
  transaction,
  categories,
  onPress,
}: {
  transaction: Transaction;
  categories: Category[];
  onPress: () => void;
}) {
  const colors = useTheme();
  const isSplit = transaction.splits.length > 1;

  return (
    <TouchableOpacity onPress={onPress}>
      <View style={[styles.txRow, { borderBottomColor: colors.line }]}>
        <TxIcon
          label={initials(transaction.description)}
          tone={transaction.amount > 0 ? 'solid' : transaction.splits.some((s) => !s.category_id) ? 'neutral' : 'accent'}
        />
        <View style={{ flex: 1 }}>
          <Text style={[styles.merchant, { color: colors.ink }]} numberOfLines={1}>
            {transaction.description}
          </Text>
          <View style={styles.chips}>
            {isSplit ? (
              transaction.splits.map((s) => (
                <Chip key={s.id} tone="accent">
                  {categoryLabel(categories, s.category_id)} · {formatKr(s.amount)}
                </Chip>
              ))
            ) : (
              <Chip>{categoryLabel(categories, transaction.splits[0]?.category_id ?? null)}</Chip>
            )}
          </View>
        </View>
        <Text style={[styles.amt, { color: transaction.amount > 0 ? colors.good : colors.ink }]}>
          {formatKr(transaction.amount)}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  filterRow: { flexGrow: 0, marginBottom: -6 },
  pill: { paddingVertical: 6, paddingHorizontal: 13, borderRadius: 20 },
  txRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  merchant: { fontSize: 14, fontWeight: '500' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 5, marginTop: 4 },
  amt: { fontSize: 14, fontWeight: '600' },
});
