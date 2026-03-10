import type { NextApiRequest, NextApiResponse } from "next";
import api from "../../../api/client";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const code = req.query.code as string;
  if (!code) {
    res.status(400).json({ error: "missing_code" });
    return;
  }

  try {
    const response = await api.post("/auth/discord/callback", { code });
    res.setHeader("Set-Cookie", `rr_token=${response.data.access_token}; Path=/; HttpOnly; SameSite=Lax`);
    res.redirect("/servers");
  } catch {
    res.status(500).json({ error: "oauth_failed" });
  }
}
