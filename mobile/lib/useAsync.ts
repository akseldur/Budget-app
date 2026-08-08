import { useCallback, useEffect, useState } from 'react';

// Enkel data-hook uten ekstern avhengighet - appen er liten nok til at
// react-query e.l. ikke gir nok verdi til å veie opp for enda et bibliotek.
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        setData(await fn());
      } catch (e) {
        setError(e as Error);
      } finally {
        if (isRefresh) setRefreshing(false);
        else setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    deps,
  );

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, loading, refreshing, refresh: () => load(true), reload: () => load(false) };
}
