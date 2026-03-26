"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { ChartData } from "@/lib/api";

const PERIODS = [
  { label: "1ヶ月", value: "1mo" },
  { label: "3ヶ月", value: "3mo" },
  { label: "6ヶ月", value: "6mo" },
  { label: "1年", value: "1y" },
  { label: "2年", value: "2y" },
  { label: "5年", value: "5y" },
];

interface Props {
  initialData: ChartData;
  code: string;
}

export default function StockChart({ initialData, code }: Props) {
  const [chartData, setChartData] = useState<ChartData>(initialData);
  const [period, setPeriod] = useState("1y");
  const [loading, setLoading] = useState(false);

  const changePeriod = async (p: string) => {
    if (p === period) return;
    setPeriod(p);
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/chart/${code}?period=${p}`
      );
      const json = await res.json();
      setChartData(json.data);
    } catch {
      // 失敗時は既存データを維持
    } finally {
      setLoading(false);
    }
  };

  const { candles, summary } = chartData;
  const firstClose = candles[0]?.close ?? null;
  const isUp = summary.change_pct != null && summary.change_pct >= 0;

  const chartPoints = candles.map((c) => ({
    date: c.date,
    close: c.close,
  }));

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          株価チャート
        </h2>
        <div className="flex gap-1">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => changePeriod(p.value)}
              className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                period === p.value
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* サマリー */}
      <div className="mt-3 flex flex-wrap gap-4 text-sm">
        <span className="font-bold text-gray-900">
          ¥{summary.latest_close?.toLocaleString() ?? "—"}
        </span>
        {summary.change_pct != null && (
          <span className={`font-medium ${isUp ? "text-red-500" : "text-blue-500"}`}>
            {isUp ? "▲" : "▼"} {Math.abs(summary.change_pct).toFixed(2)}%（期間）
          </span>
        )}
        <span className="text-gray-500 text-xs self-center">
          {summary.period_start} 〜 {summary.period_end}
        </span>
      </div>

      <div className={`mt-4 transition-opacity ${loading ? "opacity-40" : ""}`}>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={chartPoints} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10 }}
              tickFormatter={(d) => d.slice(5)}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fontSize: 10 }}
              tickFormatter={(v) => `¥${v.toLocaleString()}`}
              width={70}
            />
            <Tooltip
              formatter={(v) => [`¥${Number(v).toLocaleString()}`, "終値"]}
              labelStyle={{ fontSize: 11 }}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            {firstClose != null && (
              <ReferenceLine
                y={firstClose}
                stroke="#94a3b8"
                strokeDasharray="4 4"
              />
            )}
            <Line
              type="monotone"
              dataKey="close"
              stroke={isUp ? "#ef4444" : "#3b82f6"}
              dot={false}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
