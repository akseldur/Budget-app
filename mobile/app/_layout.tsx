import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useColorScheme } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { darkColors, lightColors } from '@/constants/theme';

export default function RootLayout() {
  const scheme = useColorScheme();
  const colors = scheme === 'dark' ? darkColors : lightColors;

  return (
    <SafeAreaProvider>
      <StatusBar style={scheme === 'dark' ? 'light' : 'dark'} />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.page },
        }}
      >
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="kategoriser" options={{ presentation: 'card' }} />
        <Stack.Screen name="ny-transaksjon" options={{ presentation: 'modal' }} />
        <Stack.Screen name="ny-kategori" options={{ presentation: 'modal' }} />
        <Stack.Screen name="kontoer" options={{ presentation: 'card' }} />
        <Stack.Screen name="transaksjon/[id]" options={{ presentation: 'modal' }} />
      </Stack>
    </SafeAreaProvider>
  );
}
