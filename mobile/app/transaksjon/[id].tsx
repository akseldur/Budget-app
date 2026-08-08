import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/Card';
import { useTheme } from '@/constants/useTheme';
import { api, ApiError, Category, Transaction } from '@/lib/api';
import { formatKr } from '@/lib/format';

interface EditableSplit {
  key: string;
  categoryId: string | null;
  amountText: string;
}

function categoryDisplayName(categories: Category[], id: string | null): string {
  if (id === null) return 'Ukategorisert';
  const category = categories.find((c) => c.id === id);
  if (!category) return 'Ukategorisert';
  const parent = categories.find((p) => p.id === category.parent_id);
  return parent ? `${parent.name} → ${category.name}` : category.name;
}

export default function SplitEditorScreen() {
  const colors = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [splits, setSplits] = useState<EditableSplit[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pickerFor, setPickerFor] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.transactions.get(id), api.categories.list()])
      .then(([t, cats]) => {
        setTransaction(t);
        setCategories(cats);
        setSplits(
          t.splits.map((s, i) => ({ key: `${i}-${s.id}`, categoryId: s.category_id, amountText: String(s.amount) })),
        );
      })
      .finally(() => setLoading(false));
  }, [id]);

  const total = transaction?.amount ?? 0;
  const sum = splits.reduce((acc, s) => acc + (parseFloat(s.amountText.replace(',', '.')) || 0), 0);
  const remaining = Math.round((total - sum) * 100) / 100;
  const balanced = Math.abs(remaining) < 0.005;

  function updateSplit(key: string, patch: Partial<EditableSplit>) {
    setSplits((prev) => prev.map((s) => (s.key === key ? { ...s, ...patch } : s)));
  }

  function addSplit() {
    setSplits((prev) => [
      ...prev,
      { key: `new-${prev.length}-${Date.now()}`, categoryId: null, amountText: remaining ? String(remaining) : '0' },
    ]);
  }

  function removeSplit(key: string) {
    setSplits((prev) => prev.filter((s) => s.key !== key));
  }

  async function save() {
    if (!balanced || saving) return;
    setSaving(true);
    setError(null);
    try {
      await api.transactions.updateSplits(
        id,
        splits.map((s) => ({ category_id: s.categoryId, amount: parseFloat(s.amountText.replace(',', '.')) || 0 })),
      );
      router.back();
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : 'Noe gikk galt, prøv igjen.');
    } finally {
      setSaving(false);
    }
  }

  if (loading || !transaction) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: colors.page }]}>
        <ActivityIndicator style={{ marginTop: 60 }} color={colors.accent} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.page }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={{ color: colors.accentStrong, fontWeight: '600' }}>Avbryt</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.ink }]}>Splitt transaksjon</Text>
        <TouchableOpacity onPress={save} disabled={!balanced || saving}>
          <Text style={{ color: balanced ? colors.accentStrong : colors.inkFaint, fontWeight: '700' }}>
            {saving ? '…' : 'Lagre'}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={{ paddingHorizontal: 16, gap: 14 }}>
        <Text style={{ color: colors.inkSoft, fontSize: 13 }} numberOfLines={1}>
          {transaction.description}
        </Text>

        <Card>
          <Text style={{ color: colors.ink, fontSize: 18, fontWeight: '700' }}>{formatKr(total)} totalt</Text>
          <Text style={{ color: colors.inkFaint, fontSize: 12, marginTop: 2, marginBottom: 10 }}>
            Delt på {splits.length} {splits.length === 1 ? 'kategori' : 'kategorier'}
          </Text>

          {splits.map((s) => (
            <View key={s.key} style={[styles.splitLine, { borderBottomColor: colors.line }]}>
              <TouchableOpacity style={{ flex: 1 }} onPress={() => setPickerFor(s.key)}>
                <Text style={{ color: colors.ink, fontSize: 13 }}>{categoryDisplayName(categories, s.categoryId)}</Text>
              </TouchableOpacity>
              <TextInput
                style={[styles.amountInput, { color: colors.ink, borderColor: colors.line }]}
                value={s.amountText}
                onChangeText={(text) => updateSplit(s.key, { amountText: text })}
                keyboardType="numbers-and-punctuation"
              />
              {splits.length > 1 && (
                <TouchableOpacity onPress={() => removeSplit(s.key)} hitSlop={8}>
                  <Text style={{ color: colors.critical, fontSize: 16 }}>×</Text>
                </TouchableOpacity>
              )}
            </View>
          ))}

          <TouchableOpacity onPress={addSplit} style={styles.addSplit}>
            <Text style={{ color: colors.accentStrong, fontWeight: '600', fontSize: 13 }}>+ Legg til kategori</Text>
          </TouchableOpacity>
        </Card>

        <Text style={{ color: balanced ? colors.good : colors.critical, fontSize: 12, textAlign: 'center' }}>
          {balanced ? 'Summen stemmer' : `Gjenstår: ${formatKr(remaining)}`}
        </Text>
        {error && <Text style={{ color: colors.critical, fontSize: 12, textAlign: 'center' }}>{error}</Text>}
      </View>

      <Modal visible={pickerFor !== null} animationType="slide" onRequestClose={() => setPickerFor(null)}>
        <SafeAreaView style={{ flex: 1, backgroundColor: colors.page }}>
          <View style={styles.header}>
            <Text style={[styles.title, { color: colors.ink }]}>Velg kategori</Text>
            <TouchableOpacity onPress={() => setPickerFor(null)}>
              <Text style={{ color: colors.accentStrong, fontWeight: '600' }}>Lukk</Text>
            </TouchableOpacity>
          </View>
          <FlatList
            data={categories.filter((c) => c.parent_id !== null)}
            keyExtractor={(c) => c.id}
            contentContainerStyle={{ paddingHorizontal: 16 }}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={[styles.pickerRow, { borderBottomColor: colors.line }]}
                onPress={() => {
                  if (pickerFor) updateSplit(pickerFor, { categoryId: item.id });
                  setPickerFor(null);
                }}
              >
                <Text style={{ color: colors.ink, fontSize: 14 }}>{categoryDisplayName(categories, item.id)}</Text>
              </TouchableOpacity>
            )}
          />
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  title: { fontSize: 15, fontWeight: '700' },
  splitLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 9,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  amountInput: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 8, paddingVertical: 4, paddingHorizontal: 8, minWidth: 72, textAlign: 'right' },
  addSplit: { marginTop: 10 },
  pickerRow: { paddingVertical: 14, borderBottomWidth: StyleSheet.hairlineWidth },
});
