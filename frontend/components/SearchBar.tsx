"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { api, SearchResult } from "@/lib/api";

export default function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (!query.trim()) { setResults([]); setOpen(false); return; }
    timer.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await api.search(query);
        setResults(data);
        setOpen(data.length > 0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
  }, [query]);

  const go = (code: string) => {
    setOpen(false);
    setQuery("");
    router.push(`/stock/${code}`);
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    if (/^\d{4}$/.test(trimmed)) {
      go(trimmed);
    } else if (results.length > 0) {
      go(results[0].code);
    }
  };

  return (
    <div ref={ref} className="relative w-full max-w-xl">
      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="企業名または証券コードで検索（例: トヨタ / 7203）"
          className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
        />
        <button
          type="submit"
          className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 active:scale-95 transition-all"
        >
          検索
        </button>
      </form>

      {open && (
        <ul className="absolute z-50 mt-1 w-full rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
          {loading && (
            <li className="px-4 py-3 text-sm text-gray-400">検索中...</li>
          )}
          {results.map((r) => (
            <li key={r.code}>
              <button
                onClick={() => go(r.code)}
                className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm hover:bg-blue-50 transition-colors"
              >
                <span className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-600">
                  {r.code}
                </span>
                <span className="font-medium text-gray-800">{r.name || "—"}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
