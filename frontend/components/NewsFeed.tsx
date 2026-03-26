interface NewsItem {
  title: string;
  url: string;
  published_at: string | null;
  source: string;
  description: string | null;
}

interface Props {
  items: NewsItem[];
  sources: { yahoo_count: number; edinet_count: number };
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("ja-JP", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Tokyo",
    });
  } catch {
    return iso.slice(0, 10);
  }
}

function SourceBadge({ source }: { source: string }) {
  const isEdinet = source === "EDINET";
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
        isEdinet
          ? "bg-green-100 text-green-700"
          : "bg-blue-100 text-blue-700"
      }`}
    >
      {source}
    </span>
  );
}

export default function NewsFeed({ items, sources }: Props) {
  if (items.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center text-sm text-gray-400">
        ニュースが見つかりませんでした
      </div>
    );
  }

  return (
    <div>
      <div className="mb-3 flex gap-3 text-xs text-gray-400">
        {sources.yahoo_count > 0 && <span>Yahoo Finance: {sources.yahoo_count}件</span>}
        {sources.edinet_count > 0 && <span>EDINET: {sources.edinet_count}件</span>}
      </div>
      <ul className="divide-y divide-gray-100">
        {items.map((item, i) => (
          <li key={i} className="py-3">
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col gap-1"
            >
              <div className="flex items-start gap-2">
                <SourceBadge source={item.source} />
                <span className="text-sm font-medium text-gray-800 group-hover:text-blue-600 transition-colors leading-snug">
                  {item.title}
                </span>
              </div>
              {item.published_at && (
                <span className="pl-1 text-xs text-gray-400">
                  {formatDate(item.published_at)}
                </span>
              )}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
