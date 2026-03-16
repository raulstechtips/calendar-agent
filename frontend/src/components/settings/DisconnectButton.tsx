"use client";

import { useState } from "react";
import { signOut } from "next-auth/react";
import { revokeAccess } from "@/actions/settings";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

export function DisconnectButton() {
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm() {
    setLoading(true);
    setError(null);

    try {
      const result = await revokeAccess();
      if (!result.success) {
        setError(result.error ?? "Failed to disconnect");
        return;
      }
      await signOut({ redirectTo: "/login" });
    } catch {
      setError("Failed to disconnect");
    } finally {
      setLoading(false);
    }
  }

  function handleCancel() {
    setConfirming(false);
    setError(null);
  }

  if (confirming) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Are you sure? This will revoke all Google permissions and sign you out.
        </p>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <div className="flex gap-2">
          <Button
            variant="destructive"
            size="sm"
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? "Disconnecting..." : "Confirm"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <Button variant="destructive" onClick={() => setConfirming(true)}>
      Disconnect Google Account
    </Button>
  );
}
