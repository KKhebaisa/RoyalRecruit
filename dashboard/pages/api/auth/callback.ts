import type { NextApiRequest, NextApiResponse } from "next";
import axios from "axios";

// Server-side: must use Docker internal hostname, NOT localhost
const INTERNAL_API_URL = process.env.INTERNAL_API_URL || "http://api:8000";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { code } = req.query;

  if (!code || typeof code !== "string") {
    console.error("Callback: missing code param");
    return res.redirect("/?error=missing_code");
  }

  console.log(`Callback: exchanging code via ${INTERNAL_API_URL}`);

  try {
    const { data } = await axios.post(
      `${INTERNAL_API_URL}/api/auth/callback`,
      null,
      { params: { code } }
    );

    const params = new URLSearchParams({
      token:    data.access_token,
      username: data.user.username,
      avatar:   data.user.avatar ?? "",
      id:       data.user.discord_id,
    });

    return res.redirect(`/auth/success?${params.toString()}`);

  } catch (err: any) {
    const status = err?.response?.status;
    const detail = JSON.stringify(err?.response?.data ?? err?.message);
    console.error(`Callback: backend returned ${status}: ${detail}`);
    return res.redirect(`/?error=auth_failed&detail=${encodeURIComponent(detail)}`);
  }
}