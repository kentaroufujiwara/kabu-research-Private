import SearchBar from "@/components/SearchBar";

const POPULAR = [
  { code: "7203", name: "トヨタ自動車" },
  { code: "6758", name: "ソニーグループ" },
  { code: "9984", name: "ソフトバンクG" },
  { code: "6861", name: "キーエンス" },
  { code: "7974", name: "任天堂" },
  { code: "8035", name: "東京エレクトロン" },
];

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center bg-gradient-to-b from-blue-50 to-white px-4">
      <div className="mt-24 flex flex-col items-center text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">
          日本株リサーチ
        </h1>
        <p className="mt-3 text-gray-500 text-sm">
          企業名または証券コードを入力して、財務・株価情報をまとめてチェック
        </p>

        <div className="mt-8 w-full max-w-xl">
          <SearchBar />
        </div>

        {/* 人気銘柄 */}
        <div className="mt-10">
          <p className="text-xs text-gray-400 mb-3">人気銘柄</p>
          <div className="flex flex-wrap justify-center gap-2">
            {POPULAR.map((s) => (
              <a
                key={s.code}
                href={`/stock/${s.code}`}
                className="rounded-full border border-gray-200 bg-white px-4 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:border-blue-300 hover:text-blue-600 transition-colors"
              >
                {s.name}
              </a>
            ))}
          </div>
        </div>
      </div>

      <footer className="mt-auto py-6 text-center text-xs text-gray-400">
        ※ 本サービスの情報は投資判断の参考情報です。投資の最終判断はご自身でお願いします。
      </footer>
    </main>
  );
}
