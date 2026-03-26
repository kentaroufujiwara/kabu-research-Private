/**
 * デモページ: Yahoo Finance のレート制限中でもUIレイアウトを確認するためのモックデータページ
 * 本番では削除すること
 */
import CompanyOverview from "@/components/CompanyOverview";
import ValuationCard from "@/components/ValuationCard";
import FinancialChart from "@/components/FinancialChart";
import NewsFeed from "@/components/NewsFeed";
import Link from "next/link";
import { api } from "@/lib/api";

const mockCompany = {
  code: "7203",
  ticker: "7203.T",
  name: "トヨタ自動車株式会社",
  industry: "Auto Manufacturers",
  sector: "Consumer Cyclical",
  exchange: "JPX",
  market_cap: 35_800_000_000_000,
  website: "https://www.toyota.co.jp",
  address: "愛知県豊田市トヨタ町1番地",
  business_summary:
    "トヨタ自動車株式会社は、乗用車・トラック・バスなどの自動車の設計・製造・販売を行う世界最大級の自動車メーカーです。レクサスブランドも展開し、ハイブリッド・EV・燃料電池車など電動化技術のリーディングカンパニーとして知られています。",
  employees: 375_235,
  currency: "JPY",
  price: 2_843.5,
  previous_close: 2_780.0,
  "52w_high": 3_491.0,
  "52w_low": 2_185.0,
};

const mockFinancials = {
  code: "7203",
  performance: [
    { fiscal_year: "2024", revenue: 45_095_325_000_000, operating_income: 5_352_934_000_000, net_income: 4_944_933_000_000, eps: 341.7 },
    { fiscal_year: "2023", revenue: 37_154_298_000_000, operating_income: 2_725_025_000_000, net_income: 2_451_318_000_000, eps: 173.5 },
    { fiscal_year: "2022", revenue: 31_379_507_000_000, operating_income: 2_995_697_000_000, net_income: 2_850_110_000_000, eps: 198.2 },
    { fiscal_year: "2021", revenue: 27_214_594_000_000, operating_income: 2_197_748_000_000, net_income: 2_245_261_000_000, eps: 155.8 },
  ],
  valuation: {
    price: 2_843.5,
    market_cap: 35_800_000_000_000,
    per: 9.5,
    forward_per: 8.2,
    pbr: 1.12,
    dividend_yield: 2.46,
    dividend_per_share: 70.0,
    eps: 294.7,
    eps_forward: 341.0,
    ev_ebitda: 6.2,
  },
  health: {
    roe: 12.8,
    roa: 4.5,
    current_ratio: 1.22,
    debt_to_equity: 85.3,
    total_debt: 21_000_000_000_000,
    total_cash: 5_800_000_000_000,
    free_cashflow: 1_540_000_000_000,
    operating_cashflow: 3_120_000_000_000,
    equity_ratio: 30.2,
  },
};

export default async function DemoPage() {
  const news = await api.news("7203").catch(() => null);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="sticky top-0 z-40 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-4xl items-center gap-4 px-4 py-3">
          <Link href="/" className="text-sm font-semibold text-blue-600 hover:underline">
            ← 検索に戻る
          </Link>
          <span className="text-sm text-gray-600">トヨタ自動車（7203）— デモ</span>
        </div>
      </nav>

      <main className="mx-auto max-w-4xl space-y-4 px-4 py-6">
        <CompanyOverview data={mockCompany} />

        <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
            業績推移
          </h2>
          <FinancialChart performance={mockFinancials.performance} />
        </section>

        <ValuationCard data={mockFinancials} />

        {news && (
          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
              最新ニュース
            </h2>
            <NewsFeed items={news.items} sources={news.sources} />
          </section>
        )}

        <p className="text-center text-xs text-gray-400 pb-4">
          ※ このページはデモ用モックデータです。実際のデータは /stock/7203 で確認できます。
        </p>
      </main>
    </div>
  );
}
