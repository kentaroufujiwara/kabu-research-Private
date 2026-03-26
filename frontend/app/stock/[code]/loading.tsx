export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="sticky top-0 z-40 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-4xl items-center gap-4 px-4 py-3">
          <div className="h-4 w-24 animate-pulse rounded bg-gray-200" />
        </div>
      </nav>

      <main className="mx-auto max-w-4xl space-y-4 px-4 py-6">
        {/* 企業概要スケルトン */}
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex justify-between">
            <div className="space-y-2">
              <div className="h-3 w-20 animate-pulse rounded bg-gray-200" />
              <div className="h-7 w-48 animate-pulse rounded bg-gray-200" />
              <div className="h-3 w-32 animate-pulse rounded bg-gray-200" />
            </div>
            <div className="space-y-2 text-right">
              <div className="h-8 w-28 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-20 animate-pulse rounded bg-gray-200" />
            </div>
          </div>
          <div className="mt-4 grid grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        </div>

        {/* チャートスケルトン */}
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="mb-3 flex justify-between">
            <div className="h-4 w-24 animate-pulse rounded bg-gray-200" />
            <div className="flex gap-1">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-6 w-10 animate-pulse rounded-lg bg-gray-200" />
              ))}
            </div>
          </div>
          <div className="h-56 animate-pulse rounded-lg bg-gray-100" />
        </div>

        {/* 業績グラフスケルトン */}
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="mb-4 h-4 w-20 animate-pulse rounded bg-gray-200" />
          <div className="h-48 animate-pulse rounded-lg bg-gray-100" />
        </div>

        {/* バリュエーションカードスケルトン */}
        <div className="grid gap-4 sm:grid-cols-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="mb-3 h-4 w-28 animate-pulse rounded bg-gray-200" />
              <div className="grid grid-cols-2 gap-3">
                {[...Array(8)].map((_, j) => (
                  <div key={j} className="space-y-1">
                    <div className="h-3 w-16 animate-pulse rounded bg-gray-200" />
                    <div className="h-4 w-20 animate-pulse rounded bg-gray-200" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
