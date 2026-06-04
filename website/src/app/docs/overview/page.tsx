"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Static-export friendly redirect (next.config redirects are not available). */
export default function DocsOverviewRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/docs");
  }, [router]);

  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <p className="text-sm text-muted">Redirecting…</p>
    </main>
  );
}
