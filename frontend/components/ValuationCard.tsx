import { FinancialsData } from "@/lib/api";
import { formatPct, formatMultiple, formatPrice, formatJpy } from "@/lib/format";

interface Props {
  data: FinancialsData;
}

export default function ValuationCard({ data }: Props) {
  const { valuation, health } = data;

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {/* バリュエーション */}
      <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
          バリュエーション
        </h2>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
          <Item label="現在株価" value={formatPrice(valuation.price)} />
          <Item label="時価総額" value={formatJpy(valuation.market_cap)} />
          <Item label="PER（実績）" value={formatMultiple(valuation.per)} />
          <Item label="PER（予想）" value={formatMultiple(valuation.forward_per)} />
          <Item label="PBR" value={formatMultiple(valuation.pbr)} />
          <Item label="配当利回り" value={formatPct(valuation.dividend_yield)} />
          <Item label="1株配当" value={valuation.dividend_per_share != null ? `¥${valuation.dividend_per_share}` : "—"} />
          <Item label="EPS（実績）" value={valuation.eps != null ? `¥${valuation.eps}` : "—"} />
          <Item label="EV/EBITDA" value={formatMultiple(valuation.ev_ebitda)} />
        </dl>
      </section>

      {/* 財務健全性 */}
      <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
          財務健全性
        </h2>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
          <Item label="ROE" value={formatPct(health.roe)} highlight={health.roe} threshold={10} />
          <Item label="ROA" value={formatPct(health.roa)} highlight={health.roa} threshold={5} />
          <Item label="自己資本比率" value={formatPct(health.equity_ratio)} highlight={health.equity_ratio} threshold={30} />
          <Item label="流動比率" value={health.current_ratio != null ? `${health.current_ratio.toFixed(1)}倍` : "—"} />
          <Item label="D/Eレシオ" value={health.debt_to_equity != null ? `${health.debt_to_equity.toFixed(1)}%` : "—"} />
          <Item label="有利子負債" value={formatJpy(health.total_debt)} />
          <Item label="現金等" value={formatJpy(health.total_cash)} />
          <Item label="FCF" value={formatJpy(health.free_cashflow)} />
          <Item label="営業CF" value={formatJpy(health.operating_cashflow)} />
        </dl>
      </section>
    </div>
  );
}

function Item({
  label,
  value,
  highlight,
  threshold,
}: {
  label: string;
  value: string;
  highlight?: number | null;
  threshold?: number;
}) {
  const isGood =
    highlight != null && threshold != null && highlight >= threshold;
  return (
    <div>
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className={`mt-0.5 font-semibold ${isGood ? "text-green-600" : "text-gray-800"}`}>
        {value}
      </dd>
    </div>
  );
}
