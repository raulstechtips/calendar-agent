"use client";

import { signIn } from "next-auth/react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const BASE_SCOPES = "openid email profile";

interface ScopeInfo {
  label: string;
  description: string;
}

const SCOPE_LABELS: Record<string, ScopeInfo> = {
  openid: { label: "OpenID", description: "Basic identity verification" },
  email: { label: "Email", description: "View your email address" },
  profile: { label: "Profile", description: "View your basic profile info" },
  "https://www.googleapis.com/auth/calendar.events": {
    label: "Google Calendar",
    description: "Read and write calendar events",
  },
  "https://www.googleapis.com/auth/gmail.metadata": {
    label: "Gmail Metadata",
    description: "View email headers and metadata",
  },
};

interface RequestableScope {
  scope: string;
  buttonLabel: string;
}

const REQUESTABLE_SCOPES: RequestableScope[] = [
  {
    scope: "https://www.googleapis.com/auth/calendar.events",
    buttonLabel: "Grant Calendar Access",
  },
  {
    scope: "https://www.googleapis.com/auth/gmail.metadata",
    buttonLabel: "Grant Gmail Access",
  },
];

interface ScopeManagerProps {
  scopes: string[];
}

export function ScopeManager({ scopes }: ScopeManagerProps) {
  const scopeSet = new Set(scopes);

  const ungrantedScopes = REQUESTABLE_SCOPES.filter(
    (rs) => !scopeSet.has(rs.scope),
  );

  function handleGrant(scope: string) {
    const fullScope = `${BASE_SCOPES} ${scope}`;
    signIn("google", { redirectTo: "/settings" }, { scope: fullScope });
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-2">
          Granted Permissions
        </h3>
        <div className="flex flex-wrap gap-2">
          {scopes.map((scope) => {
            const info = SCOPE_LABELS[scope];
            return (
              <Badge key={scope} variant="secondary" title={scope}>
                {info?.label ?? scope}
              </Badge>
            );
          })}
          {scopes.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No permissions granted yet.
            </p>
          )}
        </div>
      </div>

      {ungrantedScopes.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">
            Available Permissions
          </h3>
          <div className="flex flex-wrap gap-2">
            {ungrantedScopes.map((rs) => (
              <Button
                key={rs.scope}
                variant="outline"
                size="sm"
                onClick={() => handleGrant(rs.scope)}
              >
                {rs.buttonLabel}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
