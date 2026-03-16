import { SessionProvider } from "next-auth/react";
import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { auth, signOut } from "../../../auth";

export default async function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await auth();

  if (!session?.user) {
    redirect("/login");
  }

  const displayName = session.user.name ?? session.user.email ?? "Account";

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 flex-col border-r border-border bg-sidebar p-4 md:flex">
        <nav className="flex flex-col gap-2">
          <span className="mb-4 text-lg font-semibold text-sidebar-foreground">
            Calendar Assistant
          </span>
          <Link
            href="/chat"
            className="rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
          >
            Chat
          </Link>
          <Link
            href="/calendar"
            className="rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
          >
            Calendar
          </Link>
          <Link
            href="/settings"
            className="rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
          >
            Settings
          </Link>
        </nav>
        <div className="mt-auto pt-4">
          <div className="flex items-center gap-2 text-sm text-sidebar-foreground">
            {session.user.image && (
              <Image
                src={session.user.image}
                alt=""
                className="h-8 w-8 rounded-full"
                width={32}
                height={32}
              />
            )}
            <span className="truncate">{displayName}</span>
          </div>
          <form
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/login" });
            }}
          >
            <button
              type="submit"
              className="mt-2 text-sm text-muted-foreground hover:text-foreground"
            >
              Sign out
            </button>
          </form>
        </div>
      </aside>
      <main className="flex-1">
        <SessionProvider
          session={session}
          refetchInterval={5 * 60}
          refetchOnWindowFocus={true}
        >
          {children}
        </SessionProvider>
      </main>
    </div>
  );
}
