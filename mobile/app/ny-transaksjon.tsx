import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/Card';
import { SectionTitle } from '@/components/SectionTitle';
import { useTheme } from '@/constants/useTheme';
import { Account, api, ApiError, Category } from '@/lib/api';

export default function NyTransaksjonScreen() {
  const colors = useTheme();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [kind, setKind] = useState<'utgift' | 'inntekt'>('utgift');
  const [amountText, setAmountText] = useState('');
  const [description, setDescription] = useState('');
  const [accountId, setAccountId] = useState<string | null>(null);
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const today = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    Promise.all([api.accounts.list(), api.categories.list()])
      .then(([accs, cats]) => {
        setAccounts(accs);
        setCategories(cats);
        if (accs.length > 0) setAccountId(accs[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  const childCategories = categories.filter((c) => c.parent_id !== null);

  async function save() {
    const parsed = parseFloat(amountText.replace(',', '.'));
    if (!accountId || !description.trim() || Number.isNaN(parsed) || parsed === 0) {
      setError('Fyll ut beløp, beskrivelse og konto.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.transactions.create({
        account_id: accountId,
        date: today,
        description: description.trim(),
        amount: kind === 'utgift' ? -Math.abs(parsed) : Math.abs(parsed),
        category_id: categoryId,
      });
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
        <Text style={[styles.title, { color: colors.ink }]}>Ny transaksjon</Text>
        <View style={{ width: 50 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.field}>
          <Text style={[styles.label, { color: colors.inkFaint }]}>BELØP</Text>
          <TextInput
            style={[styles.amountBox, { color: colors.ink, backgroundColor: colors.surface2 }]}
            value={amountText}
            onChangeText={setAmountText}
            placeholder="0"
            placeholderTextColor={colors.inkFaint}
            keyboardType="numbers-and-punctuation"
          />
        </View>

        <View style={[styles.segmented, { backgroundColor: colors.surface2 }]}>
          {(['utgift', 'inntekt'] as const).map((k) => (
            <TouchableOpacity key={k} style={{ flex: 1 }} onPress={() => setKind(k)}>
              <View
                style={[
                  styles.segment,
                  kind === k && { backgroundColor: colors.surface, shadowOpacity: 0.08 },
                ]}
              >
                <Text style={{ color: kind === k ? colors.ink : colors.inkFaint, fontWeight: '600', fontSize: 13 }}>
                  {k === 'utgift' ? 'Utgift' : 'Inntekt'}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <Card style={{ gap: 14 }}>
          <View style={styles.field}>
            <Text style={[styles.label, { color: colors.inkFaint }]}>BESKRIVELSE</Text>
            <TextInput
              style={[styles.box, { color: colors.ink, backgroundColor: colors.surface2 }]}
              value={description}
              onChangeText={setDescription}
              placeholder="Hva gjaldt det?"
              placeholderTextColor={colors.inkFaint}
            />
          </View>
          <View style={styles.field}>
            <Text style={[styles.label, { color: colors.inkFaint }]}>KONTO</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {accounts.map((a) => (
                <TouchableOpacity key={a.id} onPress={() => setAccountId(a.id)}>
                  <View
                    style={[
                      styles.accountPill,
                      {
                        backgroundColor: accountId === a.id ? colors.accentStrong : colors.surface2,
                        marginRight: 8,
                      },
                    ]}
                  >
                    <Text style={{ color: accountId === a.id ? '#fff' : colors.ink, fontSize: 12, fontWeight: '600' }}>
                      {a.bank_name}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
              {accounts.length === 0 && (
                <Text style={{ color: colors.inkFaint, fontSize: 12 }}>Ingen kontoer registrert ennå</Text>
              )}
            </ScrollView>
          </View>
        </Card>

        <SectionTitle>Kategori</SectionTitle>
        <View style={styles.grid}>
          <TouchableOpacity style={{ width: '48%' }} onPress={() => setCategoryId(null)}>
            <Card style={[styles.catBtn, categoryId === null && { borderWidth: 2, borderColor: colors.accentStrong }]}>
              <Text style={{ color: colors.inkFaint, fontSize: 11, marginBottom: 2 }}>Ukategorisert</Text>
              <Text style={{ color: colors.ink, fontWeight: '500', fontSize: 13 }}>Annet</Text>
            </Card>
          </TouchableOpacity>
          {childCategories.map((c) => {
            const parent = categories.find((p) => p.id === c.parent_id);
            return (
              <TouchableOpacity key={c.id} style={{ width: '48%' }} onPress={() => setCategoryId(c.id)}>
                <Card style={[styles.catBtn, categoryId === c.id && { borderWidth: 2, borderColor: colors.accentStrong }]}>
                  <Text style={{ color: colors.inkFaint, fontSize: 11, marginBottom: 2 }}>{parent?.name}</Text>
                  <Text style={{ color: colors.ink, fontWeight: '500', fontSize: 13 }}>{c.name}</Text>
                </Card>
              </TouchableOpacity>
            );
          })}
        </View>

        {error && <Text style={{ color: colors.critical, fontSize: 12, textAlign: 'center' }}>{error}</Text>}

        <TouchableOpacity onPress={save} disabled={saving}>
          <View style={[styles.saveBtn, { backgroundColor: colors.accentStrong }]}>
            <Text style={styles.saveBtnText}>{saving ? 'Lagrer…' : 'Lagre transaksjon'}</Text>
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
  box: { borderRadius: 10, padding: 11, fontSize: 14 },
  segmented: { flexDirection: 'row', borderRadius: 10, padding: 3 },
  segment: { paddingVertical: 7, borderRadius: 8, alignItems: 'center' },
  accountPill: { paddingVertical: 6, paddingHorizontal: 12, borderRadius: 20 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, justifyContent: 'space-between' },
  catBtn: { alignItems: 'center', paddingVertical: 12 },
  saveBtn: { padding: 14, borderRadius: 12, alignItems: 'center' },
  saveBtnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
});
