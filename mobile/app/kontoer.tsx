import { router } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/Card';
import { SectionTitle } from '@/components/SectionTitle';
import { TxIcon } from '@/components/TxIcon';
import { useTheme } from '@/constants/useTheme';
import { Account, api, FundPrice, StudentLoanSnapshot } from '@/lib/api';
import { formatDateLong, formatKr, initials } from '@/lib/format';

export default function KontoerScreen() {
  const colors = useTheme();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loan, setLoan] = useState<StudentLoanSnapshot | null>(null);
  const [fund, setFund] = useState<FundPrice | null>(null);

  function load() {
    api.accounts.list().then(setAccounts).catch(() => {});
    api.studentLoan.latest().then(setLoan).catch(() => {});
    api.funds.dnbTeknologiA().then(setFund).catch(() => {});
  }

  useEffect(load, []);

  async function connectMore() {
    await WebBrowser.openBrowserAsync(api.auth.startUrl());
    load();
  }

  function updateLoanBalance() {
    Alert.prompt?.(
      'Oppdater studielånssaldo',
      'Skriv inn ny saldo (kr)',
      async (value) => {
        const parsed = parseFloat((value ?? '').replace(',', '.'));
        if (Number.isNaN(parsed)) return;
        const updated = await api.studentLoan.create({
          balance: parsed,
          as_of_date: new Date().toISOString().slice(0, 10),
        });
        setLoan(updated);
      },
      'plain-text',
      loan ? String(loan.balance) : '',
    );
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.page }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={{ color: colors.accentStrong, fontWeight: '600' }}>‹ Tilbake</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.ink }]}>Kontoer</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <SectionTitle>Tilkoblede kontoer</SectionTitle>
        <Card style={{ padding: 4 }}>
          {accounts.length === 0 && (
            <Text style={{ color: colors.inkFaint, padding: 12, textAlign: 'center' }}>Ingen kontoer ennå.</Text>
          )}
          {accounts.map((a) => (
            <View key={a.id} style={[styles.row, { borderBottomColor: colors.line }]}>
              <TxIcon label={initials(a.bank_name)} />
              <View style={{ flex: 1 }}>
                <Text style={{ color: colors.ink, fontSize: 14, fontWeight: '500' }}>{a.bank_name}</Text>
                <Text style={{ color: colors.inkFaint, fontSize: 11 }}>{a.currency}</Text>
              </View>
              <View style={[styles.pill, { backgroundColor: colors.goodWash }]}>
                <Text style={{ color: colors.good, fontSize: 11, fontWeight: '600' }}>Tilkoblet</Text>
              </View>
            </View>
          ))}
        </Card>

        <TouchableOpacity onPress={connectMore}>
          <View style={[styles.addAccount, { borderColor: colors.line }]}>
            <Text style={{ color: colors.accentStrong, fontWeight: '600', fontSize: 13 }}>+ Koble til flere kontoer</Text>
          </View>
        </TouchableOpacity>

        <SectionTitle>Studielån</SectionTitle>
        <Card>
          <Text style={{ color: colors.inkFaint, fontSize: 11, marginBottom: 2 }}>
            Lånekassen · kun til informasjon
          </Text>
          <Text style={{ color: colors.ink, fontSize: 22, fontWeight: '700' }}>
            {loan ? formatKr(loan.balance) : '—'}
          </Text>
          <Text style={{ color: colors.inkFaint, fontSize: 11, marginTop: 4, marginBottom: 12 }}>
            {loan ? `Sist oppdatert ${formatDateLong(loan.as_of_date)} · oppgis manuelt` : 'Ikke registrert ennå'}
          </Text>
          <TouchableOpacity onPress={updateLoanBalance}>
            <View style={[styles.updateBtn, { backgroundColor: colors.surface2 }]}>
              <Text style={{ color: colors.ink, fontWeight: '600', fontSize: 13 }}>Oppdater saldo</Text>
            </View>
          </TouchableOpacity>
        </Card>

        <SectionTitle>Fond</SectionTitle>
        <Card style={{ padding: 4 }}>
          <View style={styles.row}>
            <TxIcon label="D" tone="solid" />
            <View style={{ flex: 1 }}>
              <Text style={{ color: colors.ink, fontSize: 14, fontWeight: '500' }}>{fund?.name ?? 'DNB Teknologi A'}</Text>
              <Text style={{ color: colors.inkFaint, fontSize: 11 }}>Live kurs via Yahoo Finance</Text>
            </View>
            <View style={[styles.pill, { backgroundColor: colors.goodWash }]}>
              <Text style={{ color: colors.good, fontSize: 11, fontWeight: '600' }}>Aktiv</Text>
            </View>
          </View>
        </Card>
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
  title: { fontSize: 17, fontWeight: '700' },
  scroll: { paddingHorizontal: 16, paddingBottom: 40, gap: 14 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 11,
    paddingHorizontal: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  pill: { paddingVertical: 3, paddingHorizontal: 9, borderRadius: 20 },
  addAccount: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 13,
    borderRadius: 14,
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  updateBtn: { marginTop: 4, alignItems: 'center', paddingVertical: 10, borderRadius: 10 },
});
