import type { AppProps } from "next/app";
import { useEffect } from "react";
import "../styles/globals.css";
import { useAuthStore } from "../lib/store";

export default function App({ Component, pageProps }: AppProps) {
  const hydrate = useAuthStore((s) => s.hydrate);
  useEffect(() => { hydrate(); }, []);
  return <Component {...pageProps} />;
}
