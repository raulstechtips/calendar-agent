import type { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";
import { CalendarDays } from "lucide-react";
import { redirect } from "next/navigation";
import { auth, signOut } from "../../../auth";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { SidebarNav } from "@/components/layout/SidebarNav";

function getE2EMockSession(): Session {
  return {
    user: {
      id: "e2e-user",
      name: "Test User",
      email: "test@example.com",
      image: null,
    },
    accessToken: "e2e-mock-access-token",
    idToken: "e2e-mock-id-token",
    expires: new Date(Date.now() + 86_400_000).toISOString(),
  };
}

function getInitials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default async function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const isE2E =
    process.env.NODE_ENV !== "production" &&
    process.env.E2E_MOCK_SESSION === "true";
  const session = isE2E ? getE2EMockSession() : await auth();

  if (!session?.user) {
    redirect("/login");
  }

  const displayName = session.user.name ?? session.user.email ?? "Account";

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border/70 bg-sidebar p-4 md:flex">
        <div className="mb-8 flex items-center gap-2.5 px-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary shadow-sm">
            <CalendarDays className="size-4 text-primary-foreground" />
          </div>
          <span className="text-base font-semibold tracking-tight text-sidebar-foreground">
            Calendar Assistant
          </span>
        </div>
        <div className="flex-1 overflow-y-auto">
          <SidebarNav />
        </div>
        <div className="shrink-0 border-t border-border/70 pt-4">
          <div className="flex items-center gap-2.5 px-2 text-sm text-sidebar-foreground">
            <Avatar>
              {session.user.image ? (
                <AvatarImage src={session.user.image} alt={displayName} />
              ) : null}
              <AvatarFallback>{getInitials(session.user.name)}</AvatarFallback>
            </Avatar>
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-sm font-medium">{displayName}</span>
              <form
                action={async () => {
                  "use server";
                  await signOut({ redirectTo: "/login" });
                }}
              >
                <button
                  type="submit"
                  className="text-xs text-muted-foreground transition-colors hover:text-destructive"
                >
                  Sign out
                </button>
              </form>
            </div>
          </div>
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
