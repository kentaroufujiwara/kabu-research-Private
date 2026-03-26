import Link from "next/link";
import { api } from "@/lib/api";
import CompanyOverview from "@/components/CompanyOverview";
import ValuationCard from "@/components/ValuationCard";
import FinancialChart from "@/components/FinancialChart";
import StockChart from "@/components/StockChart";
import NewsFeed from "@/components/NewsFeed";
import ErrorCard from "@/components/ErrorCard";

interface Props {
  params: Promise<{ code: string }>;
}

export default async function StockPage({ params }: Props) {
  const { code } = await params;

  const [companyResult, financialsResult, chartResult, newsResult] =
    await Promise.allSettled([
      api.company(code),
      api.financials(code),
      api.chart(code, "1y"),
      api.news(code),
    ]);

  const company   = companyResult.status   === "fulfilled" ? companyResult.value   : null;
  const financials = financialsResult.status === "fulfilled" ? financialsResult.value : null;
  const chart     = chartResult.status     === "fulfilled" ? chartResult.value     : null;
  const news      = newsResult.status      === "fulfilled" ? newsResult.value      : null;

  const companyError =
    companyResult.status === "rejected" ? (companyResult.reason as Error).message : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ナビ */}
      <nav className="sticky top-0 z-40 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-4xl items-center gap-4 px-4 py-3">
          <Link href="/" className="text-sm font-semibold text-blue-600 hover:underline">
            ← 検索に戻る
          </Link>
          {company && (
            <span className="text-sm text-gray-600">
              {company.name}（{code}）
            </span>
          )}
        </div>
      </nav>

      <main className="mx-auto max-w-4xl space-y-4 px-4 py-6">
        {/* 企業概要 */}
        {companyError ? (
          <ErrorCard message={companyError} />
        ) : company ? (
          <CompanyOverview data={company} />
        ) : null}

        {/* 株価チャート */}
        {chart && <StockChart initialData={chart} code={code} />}

        {/* 業績グラフ */}
        {financials && (
          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
              業績推移
            </h2>
            <FinancialChart performance={financials.performance} />
          </section>
        )}

        {/* バリュエーション・財務健全性 */}
        {financials && <ValuationCard data={financials} />}

        {/* ニュース */}
        {news && (
          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
              最新ニュース
            </h2>
            <NewsFeed items={news.items} sources={news.sources} />
          </section>
        )}

        {/* 免責 */}
        <p className="text-center text-xs text-gray-400 pb-4">
          ※ 本情報は投資判断の参考情報です。データは yfinance 経由で取得しており、遅延・誤差が生じる場合があります。
          投資の最終判断はご自身でお願いします。
        </p>
      </main>
    </div>
  );
}
