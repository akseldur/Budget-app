// Tynn klient mot backend-API-et. Typene her speiler Pydantic-modellene i
// backend/app/routes/*.py - hold dem i sync manuelt inntil evt. kodegenerering.

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.EXPO_PUBLIC_API_KEY ?? '';

export class ApiError extends Error {
  status: number;
  detail: unknown;
  reconnectRequired: boolean;

  constructor(status: number, detail: unknown) {
    const reconnectRequired =
      typeof detail === 'object' && detail !== null && (detail as Record<string, unknown>).reconnect_required === true;
    super(typeof detail === 'string' ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
    this.reconnectRequired = reconnectRequired;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = (await response.json()).detail;
    } catch {
      detail = await response.text();
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type BudgetStatus = 'green' | 'yellow' | 'red';

export interface Account {
  id: string;
  bank_name: string;
  account_number: string;
  currency: string;
  enablebanking_account_uid: string;
}

export interface Balance {
  amount: number;
  currency: string;
  balance_type: string;
}

export interface Split {
  id: string;
  category_id: string | null;
  amount: number;
}

export interface Transaction {
  id: string;
  account_id: string;
  date: string;
  description: string;
  amount: number;
  splits: Split[];
}

export interface Category {
  id: string;
  name: string;
  parent_id: string | null;
}

export interface BudgetLine {
  id: string;
  month: string;
  category_id: string;
  planned_amount: number;
}

export interface CategoryForecast {
  category_id: string;
  category_name: string;
  spent_so_far: number;
  projected: number;
  planned_amount: number;
  status: BudgetStatus;
}

export interface FundPrice {
  symbol: string;
  name: string;
  price: number;
  currency: string;
}

export interface StudentLoanSnapshot {
  id: string;
  balance: number;
  as_of_date: string;
}

export const api = {
  accounts: {
    list: () => request<Account[]>('/accounts'),
    register: (body: { enablebanking_account_uid: string; bank_name: string }) =>
      request<Account>('/accounts/register', { method: 'POST', body: JSON.stringify(body) }),
    balance: (accountId: string) => request<Balance>(`/accounts/${accountId}/balance`),
  },
  transactions: {
    list: () => request<Transaction[]>('/transactions'),
    get: (transactionId: string) => request<Transaction>(`/transactions/${transactionId}`),
    syncForAccount: (accountId: string) =>
      request<Transaction[]>(`/accounts/${accountId}/sync-transactions`, { method: 'POST' }),
    updateSplits: (transactionId: string, splits: { category_id: string | null; amount: number }[]) =>
      request<Transaction>(`/transactions/${transactionId}/splits`, {
        method: 'PUT',
        body: JSON.stringify(splits),
      }),
    create: (body: { account_id: string; date: string; description: string; amount: number; category_id: string | null }) =>
      request<Transaction>('/transactions', { method: 'POST', body: JSON.stringify(body) }),
  },
  categories: {
    list: () => request<Category[]>('/categories'),
  },
  budget: {
    upsertLine: (body: { month: string; category_id: string; planned_amount: number }) =>
      request<BudgetLine>('/budget-lines', { method: 'PUT', body: JSON.stringify(body) }),
    status: (month: string) => request<CategoryForecast[]>(`/budget/status?month=${month}`),
  },
  funds: {
    dnbTeknologiA: () => request<FundPrice>('/funds/dnb-teknologi-a'),
  },
  studentLoan: {
    latest: () =>
      request<StudentLoanSnapshot>('/student-loan-snapshots/latest').catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      }),
    create: (body: { balance: number; as_of_date: string }) =>
      request<StudentLoanSnapshot>('/student-loan-snapshots', { method: 'POST', body: JSON.stringify(body) }),
  },
  auth: {
    startUrl: () => `${API_URL}/auth/enablebanking/start`,
  },
};
