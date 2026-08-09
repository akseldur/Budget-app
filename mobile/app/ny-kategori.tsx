import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/Card';
import { useTheme } from '@/constants/useTheme';
import { api, ApiError, Category } from '@/lib/api';
import { formatMonthYear } from '@/lib/format';

const NY_KATEGORI = '__ny__';

export default function NyKategoriScreen() {
  const colors = useTheme();
  const { month, categoryId: initialCategoryId, plannedAmount } = useLocalSearchParams<{
    month: string;
    categoryId?: string;
    plannedAmount?: string;
  }>();

  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categoryId, setCategoryId] = useState<string | null>(initialCategoryId ?? null);
  const [amountText, setAmountText] = useState(plannedAmount ?? '');
  const [newParentName, setNewParentName] = useState('');
  const [newChildName, setNewChildName] = useState('');

  useEffect(() => {
    api.categories
      .list()
      .then(setCategories)
      .finally(() => setLoading(false));
  }, []);

  const childCategories = categories.filter((c) => c.parent_id !== null);
  const parentNames = useMemo(
    () => Array.from(new Set(categories.filter((c) => c.parent_id === null).map((c) => c.name))),
    [categories],
  );
  const creatingNew = categoryId === NY_KATEGORI;

  async function save() {
    const parsed = parseFloat(amountText.replace(',', '.'));
    if (Number.isNaN(parsed) || parsed <= 0) {
      setError('Beløpet må være større enn 0.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      let targetCategoryId = categoryId;

      if (creatingNew) {
        const parent = newParentName.trim();
        const name = newChildName.trim();
        if (!parent || !name) {
          setError('Fyll ut både gruppe og navn på kategorien.');
          setSaving(false);
          return;
        }
        const created = await api.categories.create({ parent_name: parent, name });
        targetCategoryId = created.id;
      }

      if (!targetCategoryId) {
        setError('Velg en kategori.');
        setSaving(false);
        return;
      }

      await api.budget.upsertLine({ month, category_id: targetCategoryId, planned_amount: parsed });
      router.back();
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : 'Noe gikk galt, prøv igjen.');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
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
        <Text style={[styles.title, { color: colors.ink }]}>Kategori</Text>
        <View style={{ width: 50 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={{ color: colors.inkSoft, fontSize: 13, textAlign: 'center' }}>
          {formatMonthYear(month)}
        </Text>

        <View style={styles.field}>
          <Text style={[styles.label, { color: colors.inkFaint }]}>PLANLAGT BELØP</Text>
          <TextInput
            style={[styles.amountBox, { color: colors.ink, backgroundColor: colors.surface2 }]}
            value={amountText}
            onChangeText={setAmountText}
            placeholder="0"
            placeholderTextColor={colors.inkFaint}
            keyboardType="numbers-and-punctuation"
          />
        </View>

        <Text style={{ color: colors.inkFaint, fontSize: 12, marginLeft: 2 }}>Kategori</Text>
        <View style={styles.grid}>
          {childCategories.map((c) => {
            const parent = categories.find((p) => p.id === c.parent_id);
            return (
              <TouchableOpacity key={c.id} style={{ width: '48%' }} onPress={() => setCategoryId(c.id)}>
                <Card
                  style={[styles.catBtn, categoryId === c.id && { borderWidth: 2, borderColor: colors.accentStrong }]}
                >
                  <Text style={{ color: colors.inkFaint, fontSize: 11, marginBottom: 2 }}>{parent?.name}</Text>
                  <Text style={{ color: colors.ink, fontWeight: '500', fontSize: 13 }}>{c.name}</Text>
                </Card>
              </TouchableOpacity>
            );
          })}
          <TouchableOpacity style={{ width: '48%' }} onPress={() => setCategoryId(NY_KATEGORI)}>
            <Card style={[styles.catBtn, creatingNew && { borderWidth: 2, borderColor: colors.accentStrong }]}>
              <Text style={{ color: colors.accentStrong, fontWeight: '600', fontSize: 13 }}>+ Ny kategori</Text>
            </Card>
          </TouchableOpacity>
        </View>

        {creatingNew && (
          <View style={styles.newCategory}>
            <View style={styles.field}>
              <Text style={[styles.label, { color: colors.inkFaint }]}>GRUPPE</Text>
              <TextInput
                style={[styles.textInput, { color: colors.ink, backgroundColor: colors.surface2 }]}
                value={newParentName}
                onChangeText={setNewParentName}
                placeholder="F.eks. Bolig, Mat, Fritid"
                placeholderTextColor={colors.inkFaint}
              />
              {parentNames.length > 0 && (
                <View style={styles.chipRow}>
                  {parentNames.map((name) => (
                    <TouchableOpacity key={name} onPress={() => setNewParentName(name)}>
                      <View style={[styles.chip, { backgroundColor: colors.surface2 }]}>
                        <Text style={{ color: colors.inkSoft, fontSize: 12 }}>{name}</Text>
                      </View>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>

            <View style={styles.field}>
              <Text style={[styles.label, { color: colors.inkFaint }]}>KATEGORINAVN</Text>
              <TextInput
                style={[styles.textInput, { color: colors.ink, backgroundColor: colors.surface2 }]}
                value={newChildName}
                onChangeText={setNewChildName}
                placeholder="F.eks. Strøm, Kino, Klær"
                placeholderTextColor={colors.inkFaint}
              />
            </View>
          </View>
        )}

        {error && <Text style={{ color: colors.critical, fontSize: 12, textAlign: 'center' }}>{error}</Text>}

        <TouchableOpacity onPress={save} disabled={saving}>
          <View style={[styles.saveBtn, { backgroundColor: colors.accentStrong }]}>
            <Text style={styles.saveBtnText}>{saving ? 'Lagrer…' : 'Lagre'}</Text>
          </View>
        </TouchableOpacity>
      </ScrollView>
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
  scroll: { paddingHorizontal: 16, paddingBottom: 40, gap: 14 },
  field: { gap: 5 },
  label: { fontSize: 11, fontWeight: '600', letterSpacing: 0.3 },
  amountBox: { borderRadius: 10, padding: 14, fontSize: 24, fontWeight: '700', textAlign: 'center' },
  textInput: { borderRadius: 10, padding: 12, fontSize: 14 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, justifyContent: 'space-between' },
  catBtn: { alignItems: 'center', paddingVertical: 12, justifyContent: 'center', minHeight: 52 },
  newCategory: { gap: 14 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 6 },
  chip: { borderRadius: 8, paddingVertical: 5, paddingHorizontal: 10 },
  saveBtn: { padding: 14, borderRadius: 12, alignItems: 'center' },
  saveBtnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
});
