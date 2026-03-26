"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { PerformanceRow } from "@/lib/api";

interface Props {
  performance: PerformanceRow[];
}

function toOku(val: number | null): number | null {
  if (val == null) return null;
  return Math.round(val / 1e8);
}

export default function FinancialChart({ performance }: Props) {
  if (!performance || performance.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-gray-400">
        業績データがありません
      </div>
    );
  }

  const data = [...performance].reverse().map((row) => ({
    year: `${row.fiscal_year}年`,
    売上高: toOku(row.revenue),
    営業利益: toOku(row.operating_income),
    純利益: toOku(row.net_income),
    EPS: row.eps,
  }));

  return (
    <div className="space-y-6">
      {/* 売上・利益 */}
      <div>
        <p className="mb-2 text-xs text-gray-500">単位：億円</p>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v.toLocaleString()} />
            <Tooltip
              formatter={(v) => [`${Number(v).toLocaleString()}億円`]}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="売上高" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="営業利益" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="純利益" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* EPS */}
      {data.some((d) => d.EPS != null) && (
        <div>
          <p className="mb-2 text-xs text-gray-500">EPS（円）</p>
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v) => [`¥${v}`]}
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
              />
              <Bar dataKey="EPS" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
