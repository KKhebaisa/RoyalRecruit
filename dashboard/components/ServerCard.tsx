export default function ServerCard({ server, onSelect }: { server: any; onSelect: (id: string) => void }) {
  return (
    <button className="w-full rounded-lg border border-slate-700 p-4 text-left hover:bg-slate-900" onClick={() => onSelect(server.id)}>
      <p className="font-semibold">{server.name}</p>
      <p className="text-sm text-slate-400">ID: {server.id}</p>
    </button>
  );
}
