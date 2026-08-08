import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/Card';
import { SectionTitle } from '@/components/SectionTitle';
import { TxIcon } from '@/components/TxIcon';
import { useTheme } from '@/constants/useTheme';
import { api, Category, Transaction } from '@/lib/api';
import { formatDateLong, formatKr, initials } from '@/lib/format';

async function loadData() {
  const [transactions, categories] = await Promise.all([api.transactions.list(), api.categories.list()]);
  const uncategorized = transactions.filter((t) => t.splits.some((s) => s.category_id === null));
  return { uncategorized, categories };
}

export default function KategoriserScreen() {
  const colors = useTheme();
  const [loading, setLoading] = useState(true);
  const [queue, setQueue] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [index, setIndex] = useState(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData()
      .then(({ uncategorized, categories }) => {
        setQueue(uncategorized);
        setCategories(categories);
      })
      .finally(() => setLoading(false));
  }, []);

  const current = queue[index];
  const childCategories = useMemo(() => categories.filter((c) => c.parent_id !== null), [categories]);

  async function chooseCategory(categoryId: string) {
    if (!current || saving) return;
    setSaving(true);
    try {
      await api.transactions.updateSplits(current.id, [{ category_id: categoryId, amount: current.amount }]);
      advance();
    } finally {
      setSaving(false);
    }
  }

  function advance() {
    if (index + 1 >= queue.length) {
      router.back();
    } else {
      setIndex(index + 1);
    }
  }

  if (loading) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: colors.page }]}>
        <ActivityIndicator style={{ marginTop: 60 }} color={colors.accent} />
      </SafeAreaView>
    );
  }

  if (!current) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: colors.page }]}>
        <View style={styles.emptyState}>
          <Text style={{ color: colors.ink, fontSize: 16, fontWeight: '600' }}>Alt er kategorisert 🎉</Text>
          <TouchableOpacity onPress={() => router.back()} style={{ marginTop: 16 }}>
            <Text style={{ color: colors.accentStrong, fontWeight: '600' }}>Tilbake</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.page }]}>
      <View style={styles.header}>
        <Text style={[styles.eyebrow, { color: colors.inkFaint }]}>{queue.length} venter</Text>
        <Text style={[styles.title, { color: colors.ink }]}>Kategoriser</Text>
      </View>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.counterRow}>
          <Text style={{ color: colors.inkSoft, fontWeight: '600', fontSize: 13 }}>
            {index + 1} av {queue.length}
          </Text>
          <View style={styles.dots}>
            {queue.map((_, i) => (
              <View
                key={i}
                style={[styles.dot, { backgroundColor: i <= index ? colors.accent : colors.line }]}
              />
            ))}
          </View>
        </View>

        <Card style={styles.triageCard}>
          <TxIcon label={initials(current.description)} tone="neutral" size={52} />
          <Text style={[styles.merchant, { color: colors.ink }]}>{current.description}</Text>
          <Text style={[styles.meta, { color: colors.inkFaint }]}>{formatDateLong(current.date)}</Text>
          <Text style={[styles.amt, { color: colors.ink }]}>{formatKr(current.amount)}</Text>
        </Card>

        <View style={styles.grid}>
          {childCategories.map((c) => {
            const parent = categories.find((p) => p.id === c.parent_id);
            return (
              <TouchableOpacity key={c.id} style={{ width: '48%' }} onPress={() => chooseCategory(c.id)} disabled={saving}>
                <Card style={styles.catBtn}>
                  <Text style={[styles.catParent, { color: colors.inkFaint }]}>{parent?.name}</Text>
                  <Text style={{ color: colors.ink, fontWeight: '500', fontSize: 13 }}>{c.name}</Text>
                </Card>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.actions}>
          <TouchableOpacity onPress={() => router.push(`/transaksjon/${current.id}`)}>
            <Text style={{ color: colors.accentStrong, fontWeight: '600', fontSize: 13 }}>Del på flere</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={advance}>
            <Text style={{ color: colors.inkFaint, fontWeight: '600', fontSize: 13 }}>Hopp over</Text>
          </TouchableOpacity>
        </View>

        {queue.length > index + 1 && (
          <>
            <SectionTitle>Neste i køen</SectionTitle>
            <Card style={{ padding: 4 }}>
              {queue.slice(index + 1, index + 3).map((t) => (
                <View key={t.id} style={[styles.queueRow, { borderBottomColor: colors.line }]}>
                  <TxIcon label={initials(t.description)} tone="neutral" size={28} />
                  <Text style={{ flex: 1, color: colors.ink, fontSize: 13 }} numberOfLines={1}>
                    {t.description}
                  </Text>
                  <Text style={{ color: colors.ink, fontSize: 13, fontWeight: '600' }}>{formatKr(t.amount)}</Text>
                </View>
              ))}
            </Card>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 10 },
  eyebrow: { fontSize: 12, marginBottom: 2 },
  title: { fontSize: 24, fontWeight: '700' },
  scroll: { paddingHorizontal: 16, paddingBottom: 40, gap: 14 },
  emptyState: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  counterRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  dots: { flexDirection: 'row', gap: 4 },
  dot: { width: 6, height: 6, borderRadius: 3 },
  triageCard: { alignItems: 'center', paddingVertical: 26 },
  merchant: { fontSize: 16, fontWeight: '600', marginTop: 10 },
  meta: { fontSize: 12, marginTop: 2, marginBottom: 8 },
  amt: { fontSize: 28, fontWeight: '700' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, justifyContent: 'space-between' },
  catBtn: { alignItems: 'center', paddingVertical: 12 },
  catParent: { fontSize: 11, marginBottom: 2 },
  actions: { flexDirection: 'row', justifyContent: 'center', gap: 24 },
  queueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 8,
    paddingHorizontal: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    opacity: 0.7,
  },
});
