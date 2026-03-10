import { PropsWithChildren } from "react";

export default function Layout({ children }: PropsWithChildren) {
  return <main className="mx-auto max-w-5xl p-6">{children}</main>;
}
