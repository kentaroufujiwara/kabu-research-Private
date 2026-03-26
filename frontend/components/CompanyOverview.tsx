import { CompanyData } from "@/lib/api";
import { formatPrice, formatJpy, formatEmployees } from "@/lib/format";

interface Props {
  data: CompanyData;
}

export default function CompanyOverview({ data }: Props) {
  const priceChange =
    data.price != null && data.previous_close != null
      ? data.price - data.previous_close
      : null;
  const priceChangePct =
    priceChange != null && data.previous_close
      ? (priceChange / data.previous_close) * 100
      : null;
  const isUp = priceChange != null && priceChange >= 0;

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      {/* ヘッダー */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="rounded bg-gray-100 px-2 py-0.5 font-mono">{data.code}</span>
            <span>{data.exchange}</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">{data.name}</h1>
          <div className="mt-1 flex flex-wrap gap-2 text-xs text-gray-500">
            {data.sector && <span>{data.sector}</span>}
            {data.sector && data.industry && <span>›</span>}
            {data.industry && <span>{data.industry}</span>}
          </div>
        </div>

        {/* 現在株価 */}
        {data.price != null && (
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900">
              {formatPrice(data.price)}
            </div>
            {priceChange != null && (
              <div className={`mt-0.5 text-sm font-medium ${isUp ? "text-red-500" : "text-blue-500"}`}>
                {isUp ? "+" : ""}
                {priceChange.toFixed(1)} ({isUp ? "+" : ""}
                {priceChangePct?.toFixed(2)}%)
              </div>
            )}
            <div className="mt-0.5 text-xs text-gray-400">前日比</div>
          </div>
        )}
      </div>

      {/* 指標バー */}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="時価総額" value={formatJpy(data.market_cap)} />
        <Metric label="52週高値" value={formatPrice(data["52w_high"])} />
        <Metric label="52週安値" value={formatPrice(data["52w_low"])} />
        <Metric label="従業員数" value={formatEmployees(data.employees)} />
      </div>

      {/* 住所・ウェブサイト */}
      {(data.address || data.website) && (
        <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
          {data.address && <span>📍 {data.address}</span>}
          {data.website && (
            <a
              href={data.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              🌐 公式サイト
            </a>
          )}
        </div>
      )}

      {/* 事業内容 */}
      {data.business_summary && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-medium text-gray-700">
            事業内容
          </summary>
          <p className="mt-2 text-sm leading-relaxed text-gray-600 line-clamp-5">
            {data.business_summary}
          </p>
        </details>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-gray-50 px-3 py-2">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-0.5 font-semibold text-gray-800">{value}</div>
    </div>
  );
}
