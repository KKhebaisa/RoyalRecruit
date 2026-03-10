import Layout from "../components/Layout";

export default function Home() {
  const clientId = process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID;
  const redirect = encodeURIComponent(process.env.NEXT_PUBLIC_DISCORD_REDIRECT_URI || "http://localhost:3000/api/auth/callback");
  const oauthUrl = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&redirect_uri=${redirect}&response_type=code&scope=identify%20guilds`;

  return (
    <Layout>
      <h1 className="mb-6 text-4xl font-bold">RoyalRecruit</h1>
      <p className="mb-8 text-slate-300">Ticket and application automation for Discord alliances.</p>
      <a className="rounded bg-indigo-600 px-4 py-2 font-semibold" href={oauthUrl}>
        Login with Discord
      </a>
    </Layout>
  );
}
