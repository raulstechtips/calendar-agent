import { signIn } from "../../../../auth";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="mx-auto flex w-full max-w-sm flex-col items-center gap-6 p-8">
        <h1 className="text-2xl font-bold">Calendar Assistant</h1>
        <p className="text-center text-muted-foreground">
          Sign in to manage your calendar with AI
        </p>
        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/chat" });
          }}
        >
          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Sign in with Google
          </button>
        </form>
      </div>
    </main>
  );
}
