import { getUserProfile, getUserPreferences } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ScopeManager } from "@/components/settings/ScopeManager";
import { PreferencesForm } from "@/components/settings/PreferencesForm";
import { DisconnectButton } from "@/components/settings/DisconnectButton";
import type { UserPreferences } from "@/lib/api";

export default async function SettingsPage() {
  let scopes: string[] = [];
  let preferences: UserPreferences = { timezone: "UTC", default_calendar: "primary" };

  const [profileResult, prefsResult] = await Promise.allSettled([
    getUserProfile(),
    getUserPreferences(),
  ]);

  if (profileResult.status === "fulfilled") {
    scopes = profileResult.value.granted_scopes;
  }

  if (prefsResult.status === "fulfilled") {
    preferences = prefsResult.value;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage your Google permissions and preferences.
        </p>
      </div>

      <Separator />

      <section aria-label="Google Account">
        <Card>
          <CardHeader>
            <CardTitle>Google Account</CardTitle>
            <CardDescription>
              Manage which Google services this app can access.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScopeManager scopes={scopes} />
          </CardContent>
        </Card>
      </section>

      <section aria-label="Preferences">
        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
            <CardDescription>
              Configure your timezone and default calendar.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PreferencesForm preferences={preferences} />
          </CardContent>
        </Card>
      </section>

      <section aria-label="Danger Zone">
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="text-destructive">Danger Zone</CardTitle>
            <CardDescription>
              Disconnect your Google account and revoke all permissions.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DisconnectButton />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
