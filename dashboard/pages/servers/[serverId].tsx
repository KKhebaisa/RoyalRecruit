import Link from "next/link";
import { useRouter } from "next/router";
import Layout from "../../components/Layout";

export default function ServerDashboard() {
  const { query } = useRouter();
  const serverId = query.serverId as string;
  const links = ["tickets", "applications", "panels", "settings"];

  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-bold">Server Dashboard: {serverId}</h1>
      <div className="grid grid-cols-2 gap-4">
        {links.map((link) => (
          <Link key={link} href={`/servers/${serverId}/${link}`} className="rounded border border-slate-700 p-4 capitalize hover:bg-slate-900">
            {link}
          </Link>
        ))}
      </div>
    </Layout>
  );
}
