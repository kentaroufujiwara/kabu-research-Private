// ローカル開発: NEXT_PUBLIC_API_URL=http://localhost:8000
// 本番(Vercel): 空文字 → 同一オリジンの /api/* → vercel.json でバックエンドにリライト
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface SearchResult {
  code: string;
  name: string;
  matched_by: string;
}

export interface CompanyData {
  code: string;
  ticker: string;
  name: string;
  industry: string;
  sector: string;
  exchange: string;
  market_cap: number | null;
  website: string;
  address: string;
  business_summary: string;
  employees: number | null;
  currency: string;
  price: number | null;
  previous_close: number | null;
  "52w_high": number | null;
  "52w_low": number | null;
}

export interface PerformanceRow {
  fiscal_year: string;
  revenue: number | null;
  operating_income: number | null;
  net_income: number | null;
  eps: number | null;
}

export interface FinancialsData {
  code: string;
  performance: PerformanceRow[];
  valuation: {
    price: number | null;
    market_cap: number | null;
    per: number | null;
    forward_per: number | null;
    pbr: number | null;
    dividend_yield: number | null;
    dividend_per_share: number | null;
    eps: number | null;
    eps_forward: number | null;
    ev_ebitda: number | null;
  };
  health: {
    roe: number | null;
    roa: number | null;
    current_ratio: number | null;
    debt_to_equity: number | null;
    total_debt: number | null;
    total_cash: number | null;
    free_cashflow: number | null;
    operating_cashflow: number | null;
    equity_ratio: number | null;
  };
}

export interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface NewsItem {
  title: string;
  url: string;
  published_at: string | null;
  source: string;
  description: string | null;
}

export interface NewsData {
  code: string;
  items: NewsItem[];
  sources: { yahoo_count: number; edinet_count: number };
}

export interface ChartData {
  code: string;
  period: string;
  candles: Candle[];
  summary: {
    latest_close: number | null;
    period_start: string | null;
    period_end: string | null;
    change_pct: number | null;
    high: number | null;
    low: number | null;
  };
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 900 } });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  const json = await res.json();
  return json.data as T;
}

export const api = {
  search: async (q: string): Promise<SearchResult[]> => {
    const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(q)}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) throw new Error("検索に失敗しました");
    const json = await res.json();
    return json.results as SearchResult[];
  },
  company: (code: string) => get<CompanyData>(`/api/company/${code}`),
  financials: (code: string) => get<FinancialsData>(`/api/financials/${code}`),
  chart: (code: string, period = "1y") =>
    get<ChartData>(`/api/chart/${code}?period=${period}`),
  news: (code: string) => get<NewsData>(`/api/news/${code}`),
};
