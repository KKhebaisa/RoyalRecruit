import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../../components/Layout";
import ServerCard from "../../components/ServerCard";
import api from "../../api/client";

export default function ServersPage() {
  const [servers, setServers] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    api.get("/servers").then((res) => setServers(res.data));
  }, []);

  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-bold">Select Server</h1>
      <div className="space-y-3">
        {servers.map((server) => (
          <ServerCard key={server.discord_server_id} server={{ id: server.discord_server_id, name: `Guild ${server.discord_server_id}` }} onSelect={(id) => router.push(`/servers/${id}`)} />
        ))}
      </div>
    </Layout>
  );
}
