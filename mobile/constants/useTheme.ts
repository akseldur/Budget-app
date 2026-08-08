import { useColorScheme } from 'react-native';

import { darkColors, lightColors } from './theme';

export function useTheme() {
  const scheme = useColorScheme();
  return scheme === 'dark' ? darkColors : lightColors;
}
