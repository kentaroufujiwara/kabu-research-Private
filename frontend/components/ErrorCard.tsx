interface Props {
  message: string;
}

export default function ErrorCard({ message }: Props) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
      <span className="font-semibold">エラー: </span>{message}
    </div>
  );
}
