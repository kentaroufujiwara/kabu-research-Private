"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, CompanyData, FinancialsData, ChartData, NewsData } from "@/lib/api";
import CompanyOverview from "@/components/CompanyOverview";
import ValuationCard from "@/components/ValuationCard";
import FinancialChart from "@/components/FinancialChart";
import StockChart from "@/components/StockChart";
import NewsFeed from "@/components/NewsFeed";
import ErrorCard from "@/components/ErrorCard";

function Skeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="h-6 w-1/3 rounded bg-gray-200 mb-2" />
        <div className="h-4 w-1/4 rounded bg-gray-200 mb-4" />
        <div className="grid grid-cols-4 gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 rounded bg-gray-200" />
          ))}
        </div>
      </div>
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm h-64 bg-gray-100" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm h-48 bg-gray-100" />
    </div>
  );
}

export default function StockPage() {
  const params = useParams();
  const code = params.code as string;

  const [company, setCompany] = useState<CompanyData | null>(null);
  const [financials, setFinancials] = useState<FinancialsData | null>(null);
  const [chart, setChart] = useState<ChartData | null>(null);
  const [news, setNews] = useState<NewsData | null>(null);
  const [companyError, setCompanyError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!code) return;
    setLoading(true);
    Promise.allSettled([
      api.company(code),
      api.financials(code),
      api.chart(code, "1y"),
      api.news(code),
    ]).then(([companyResult, financialsResult, chartResult, newsResult]) => {
      if (companyResult.status === "fulfilled") setCompany(companyResult.value);
      else setCompanyError((companyResult.reason as Error).message);
      if (financialsResult.status === "fulfilled") setFinancials(financialsResult.value);
      if (chartResult.status === "fulfilled") setChart(chartResult.value);
      if (newsResult.status === "fulfilled") setNews(newsResult.value);
      setLoading(false);
    });
  }, [code]);

  return (
    <div className="min-h-screen bg-gray-50">
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
        {loading ? (
          <Skeleton />
        ) : (
          <>
            {companyError ? (
              <ErrorCard message={companyError} />
            ) : company ? (
              <CompanyOverview data={company} />
            ) : null}

            {chart && <StockChart initialData={chart} code={code} />}

            {financials && (
              <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
                  業績推移
                </h2>
                <FinancialChart performance={financials.performance} />
              </section>
            )}

            {financials && <ValuationCard data={financials} />}

            {news && (
              <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
                  最新ニュース
                </h2>
                <NewsFeed items={news.items} sources={news.sources} />
              </section>
            )}

            <p className="text-center text-xs text-gray-400 pb-4">
              ※ 本情報は投資判断の参考情報です。データは J-Quants API（JPX公式）経由で取得しており、遅延・誤差が生じる場合があります。
              投資の最終判断はご自身でお願いします。
            </p>
          </>
        )}
      </main>
    </div>
  );
}
