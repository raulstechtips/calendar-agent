import Image from "next/image";
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

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 border-r border-border bg-sidebar p-4 md:block">
        <nav className="flex flex-col gap-2">
          <span className="mb-4 text-lg font-semibold text-sidebar-foreground">
            Calendar Assistant
          </span>
          <a
            href="/chat"
            className="rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
          >
            Chat
          </a>
          <a
            href="/calendar"
            className="rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
          >
            Calendar
          </a>
          <a
            href="/settings"
            className="rounded-md px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
          >
            Settings
          </a>
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
            <span className="truncate">{session.user.name}</span>
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
      <main className="flex-1">{children}</main>
    </div>
  );
}
