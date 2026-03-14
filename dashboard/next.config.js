/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ["cdn.discordapp.com"],
  },
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_DISCORD_CLIENT_ID:
      process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID ||
      process.env.DISCORD_CLIENT_ID ||
      "",
    NEXT_PUBLIC_DISCORD_REDIRECT_URI:
      process.env.NEXT_PUBLIC_DISCORD_REDIRECT_URI ||
      process.env.DISCORD_REDIRECT_URI ||
      "http://localhost:3000/api/auth/callback",
  },
};

module.exports = nextConfig;