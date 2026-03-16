import { redirect } from "next/navigation";

import { auth } from "../../../../auth";
import ChatShell from "@/components/chat/ChatShell";

export default async function ChatPage() {
  const session = await auth();

  if (!session?.idToken) {
    redirect("/login");
  }

  return <ChatShell token={session.idToken} />;
}
