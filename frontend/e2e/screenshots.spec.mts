import path from "node:path";

import { test } from "@playwright/test";

const SCREENSHOT_DIR = path.join(import.meta.dirname, "screenshots");

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const mockSession = {
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

function createMockCalendarEvents() {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  return {
    items: [
      {
        id: "evt-1",
        summary: "Team Standup",
        start: { dateTime: makeTime(today, 9, 0) },
        end: { dateTime: makeTime(today, 9, 30) },
      },
      {
        id: "evt-2",
        summary: "Design Review",
        description: "Review new dashboard mockups with the team",
        start: { dateTime: makeTime(today, 11, 0) },
        end: { dateTime: makeTime(today, 12, 0) },
      },
      {
        id: "evt-3",
        summary: "Lunch with Sarah",
        location: "Café Milano",
        start: { dateTime: makeTime(today, 12, 30) },
        end: { dateTime: makeTime(today, 13, 30) },
      },
      {
        id: "evt-4",
        summary: "Sprint Planning",
        start: { dateTime: makeTime(today, 14, 0) },
        end: { dateTime: makeTime(today, 15, 30) },
        extendedProperties: { private: { createdByAgent: "calendar-agent" } },
      },
      {
        id: "evt-4b",
        summary: "Product Sync",
        start: { dateTime: makeTime(today, 14, 30) },
        end: { dateTime: makeTime(today, 15, 30) },
        extendedProperties: { private: { createdByAgent: "calendar-agent" } },
      },
      {
        id: "evt-5",
        summary: "Focus Time",
        start: { dateTime: makeTime(today, 16, 0) },
        end: { dateTime: makeTime(today, 17, 0) },
      },
      {
        id: "evt-6",
        summary: "1:1 with Manager",
        start: { dateTime: makeTime(addDays(today, 1), 10, 0) },
        end: { dateTime: makeTime(addDays(today, 1), 10, 30) },
      },
      {
        id: "evt-7",
        summary: "Product Demo",
        start: { dateTime: makeTime(addDays(today, 1), 15, 0) },
        end: { dateTime: makeTime(addDays(today, 1), 16, 0) },
        extendedProperties: { private: { createdByAgent: "calendar-agent" } },
      },
      {
        id: "evt-8",
        summary: "Code Review Session",
        start: { dateTime: makeTime(addDays(today, 2), 13, 0) },
        end: { dateTime: makeTime(addDays(today, 2), 14, 0) },
      },
      {
        id: "evt-9",
        summary: "Company All-Hands",
        start: { date: formatDate(addDays(today, 3)) },
        end: { date: formatDate(addDays(today, 4)) },
      },
      {
        id: "evt-10",
        summary: "Dentist Appointment",
        start: { dateTime: makeTime(addDays(today, 4), 9, 0) },
        end: { dateTime: makeTime(addDays(today, 4), 10, 0) },
      },
    ],
  };
}

function makeTime(date: Date, hours: number, minutes: number): string {
  const d = new Date(date);
  d.setHours(hours, minutes, 0, 0);
  return d.toISOString();
}

function addDays(date: Date, days: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe("UI Screenshots", () => {
  test.beforeEach(async ({ page }) => {
    // Mock client-side session validation
    await page.route("**/api/auth/session", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSession),
      }),
    );

    // Mock Google Calendar API (use regex for reliable URL matching)
    await page.route(/googleapis\.com\/calendar/, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(createMockCalendarEvents()),
      }),
    );
  });

  test("login page", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/01-login.png`,
      fullPage: true,
    });
  });

  test("chat page - empty state", async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/02-chat-empty.png`,
      fullPage: true,
    });
  });

  test("chat page - with messages", async ({ page }) => {
    await page.goto("/chat");
    await page.waitForLoadState("networkidle");

    // Type a message (it won't get a real response, but shows input state)
    const textarea = page.getByLabel("Chat message");
    await textarea.fill("What meetings do I have tomorrow?");

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/03-chat-with-input.png`,
      fullPage: true,
    });
  });

  test("calendar page - week view", async ({ page }) => {
    await page.goto("/calendar");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/04-calendar-week.png`,
      fullPage: true,
    });
  });

  test("calendar page - day view", async ({ page }) => {
    await page.goto("/calendar?view=day");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/05-calendar-day.png`,
      fullPage: true,
    });
  });

  test("settings page", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("networkidle");
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/06-settings.png`,
      fullPage: true,
    });
  });

  test("calendar page - scope required prompt", async ({ page }) => {
    // Override the calendar API mock to return 403 (insufficient scope)
    await page.route(/googleapis\.com\/calendar/, (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            errors: [
              { domain: "calendar", reason: "insufficientScope" },
            ],
          },
        }),
      }),
    );

    await page.goto("/calendar");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/07-calendar-scope-prompt.png`,
      fullPage: true,
    });
  });

  test("chat page - conversation with agent response", async ({ page }) => {
    // Mock the chat SSE endpoint to return a canned response
    await page.route("**/api/chat", (route) => {
      if (route.request().method() !== "POST") {
        return route.fallback();
      }
      const sseBody = [
        `data: ${JSON.stringify({ type: "token", content: "You have " })}`,
        `data: ${JSON.stringify({ type: "token", content: "2 meetings tomorrow" })}`,
        `data: ${JSON.stringify({ type: "token", content: ":\n\n" })}`,
        `data: ${JSON.stringify({ type: "token", content: "1. **1:1 with Manager** — 10:00 AM – 10:30 AM\n" })}`,
        `data: ${JSON.stringify({ type: "token", content: "2. **Product Demo** — 3:00 PM – 4:00 PM\n\n" })}`,
        `data: ${JSON.stringify({ type: "token", content: "Would you like me to make any changes to your schedule?" })}`,
        `data: ${JSON.stringify({ type: "done", thread_id: "thread-mock-123" })}`,
      ].join("\n") + "\n";

      return route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
        },
        body: sseBody,
      });
    });

    await page.goto("/chat");
    await page.waitForLoadState("networkidle");

    // Type and send a message
    const textarea = page.getByLabel("Chat message");
    await textarea.fill("What meetings do I have tomorrow?");
    await page.getByLabel("Send message").click();

    // Wait for the streamed response to render
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/08-chat-conversation.png`,
      fullPage: true,
    });
  });

  test("chat page - confirmation card (approve action)", async ({ page }) => {
    // Replicate the real multi-turn flow:
    // 1. User asks to schedule something
    // 2. Assistant asks "Should I do this?"
    // 3. User says "Yes"
    // 4. Assistant responds with a small text bubble + confirmation card
    //    (the small bubble above the card is a UI bug in production)
    let requestCount = 0;
    await page.route("**/api/chat", (route) => {
      if (route.request().method() !== "POST") {
        return route.fallback();
      }
      requestCount++;

      let sseBody: string;
      if (requestCount === 1) {
        // First request: assistant asks for confirmation in natural language
        sseBody = [
          `data: ${JSON.stringify({ type: "token", content: "Sure! I can create a " })}`,
          `data: ${JSON.stringify({ type: "token", content: "Team Lunch event tomorrow at noon " })}`,
          `data: ${JSON.stringify({ type: "token", content: "at Café Milano. " })}`,
          `data: ${JSON.stringify({ type: "token", content: "Should I go ahead and schedule it?" })}`,
          `data: ${JSON.stringify({ type: "done", thread_id: "thread-mock-123" })}`,
        ].join("\n") + "\n";
      } else {
        // Second request: assistant emits a small text bubble then
        // the confirmation card — reproducing the production UI bug
        // where a partial text bubble appears above the card
        sseBody = [
          `data: ${JSON.stringify({ type: "token", content: "" })}`,
          `data: ${JSON.stringify({
            type: "confirmation",
            action: "create_event",
            action_id: "action-mock-456",
            details: {
              summary: "Team Lunch",
              start: "2026-03-18 12:00:00",
              end: "2026-03-18 13:00:00",
              location: "Café Milano",
              attendees: ["sarah@example.com", "mike@example.com"],
            },
          })}`,
          `data: ${JSON.stringify({ type: "done", thread_id: "thread-mock-123" })}`,
        ].join("\n") + "\n";
      }

      return route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
        },
        body: sseBody,
      });
    });

    await page.goto("/chat");
    await page.waitForLoadState("networkidle");

    // Turn 1: User asks to schedule
    const textarea = page.getByLabel("Chat message");
    await textarea.fill("Schedule a team lunch tomorrow at noon at Café Milano");
    await page.getByLabel("Send message").click();
    await page.waitForTimeout(1000);

    // Turn 2: User confirms
    await textarea.fill("Yes, go ahead");
    await page.getByLabel("Send message").click();
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/09-chat-confirmation.png`,
      fullPage: true,
    });
  });

  test("calendar page - empty state (no events)", async ({ page }) => {
    // Override calendar API to return no events
    await page.route(/googleapis\.com\/calendar/, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [] }),
      }),
    );

    await page.goto("/calendar");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/10-calendar-empty.png`,
      fullPage: true,
    });
  });

  test("calendar page - day view with overlapping events", async ({ page }) => {
    // Override with events that overlap at the same time
    await page.route(/googleapis\.com\/calendar/, (route) => {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "ov-1",
              summary: "Team Standup",
              start: { dateTime: makeTime(today, 9, 0) },
              end: { dateTime: makeTime(today, 9, 30) },
            },
            {
              id: "ov-2",
              summary: "Design Review",
              start: { dateTime: makeTime(today, 9, 0) },
              end: { dateTime: makeTime(today, 10, 30) },
            },
            {
              id: "ov-3",
              summary: "Client Call",
              start: { dateTime: makeTime(today, 9, 15) },
              end: { dateTime: makeTime(today, 10, 0) },
            },
            {
              id: "ov-4",
              summary: "Sprint Planning",
              start: { dateTime: makeTime(today, 10, 0) },
              end: { dateTime: makeTime(today, 11, 30) },
              extendedProperties: { private: { createdByAgent: "calendar-agent" } },
            },
            {
              id: "ov-5",
              summary: "Lunch with Sarah",
              location: "Café Milano",
              start: { dateTime: makeTime(today, 12, 0) },
              end: { dateTime: makeTime(today, 13, 0) },
            },
            {
              id: "ov-6",
              summary: "Code Review",
              start: { dateTime: makeTime(today, 12, 30) },
              end: { dateTime: makeTime(today, 13, 30) },
            },
            {
              id: "ov-7",
              summary: "Focus Time",
              start: { dateTime: makeTime(today, 14, 0) },
              end: { dateTime: makeTime(today, 16, 0) },
              extendedProperties: { private: { createdByAgent: "calendar-agent" } },
            },
          ],
        }),
      });
    });

    await page.goto("/calendar?view=day");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/11-calendar-day-overlapping.png`,
      fullPage: true,
    });
  });

  test("chat page - long conversation (scroll behavior)", async ({ page }) => {
    // Mock endpoint to return multiple back-and-forth messages
    let requestCount = 0;
    await page.route("**/api/chat", (route) => {
      if (route.request().method() !== "POST") return route.fallback();
      requestCount++;
      const responses: Record<number, string> = {
        1: "You have 5 meetings today:\n\n1. **Team Standup** — 9:00 AM\n2. **Design Review** — 11:00 AM\n3. **Lunch with Sarah** — 12:30 PM\n4. **Sprint Planning** — 2:00 PM\n5. **Focus Time** — 4:00 PM\n\nWould you like me to reschedule any of these?",
        2: "Sure! I can move **Sprint Planning** to 3:00 PM and shorten it to 1 hour. That gives you a 30-minute buffer after lunch. Want me to make that change?",
        3: "Done! I've updated Sprint Planning to 3:00 PM – 4:00 PM. Your afternoon now looks like:\n\n- 12:30 PM — Lunch with Sarah\n- 2:00 PM — Free\n- 3:00 PM — Sprint Planning\n- 4:00 PM — Focus Time",
      };
      const content = responses[requestCount] ?? "Is there anything else?";
      const sseBody = [
        `data: ${JSON.stringify({ type: "token", content })}`,
        `data: ${JSON.stringify({ type: "done", thread_id: "thread-mock-123" })}`,
      ].join("\n") + "\n";
      return route.fulfill({
        status: 200,
        headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
        body: sseBody,
      });
    });

    await page.goto("/chat");
    await page.waitForLoadState("networkidle");

    const textarea = page.getByLabel("Chat message");

    // Turn 1
    await textarea.fill("What's on my schedule today?");
    await page.getByLabel("Send message").click();
    await page.waitForTimeout(800);

    // Turn 2
    await textarea.fill("Can you move Sprint Planning later?");
    await page.getByLabel("Send message").click();
    await page.waitForTimeout(800);

    // Turn 3
    await textarea.fill("Yes, make that change");
    await page.getByLabel("Send message").click();
    await page.waitForTimeout(800);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/12-chat-long-conversation.png`,
      fullPage: true,
    });
  });

  test("settings page - disconnect confirmation", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("networkidle");

    // Click "Disconnect Google Account" to show confirmation UI
    await page.getByRole("button", { name: "Disconnect Google Account" }).click();
    await page.waitForTimeout(300);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/13-settings-disconnect-confirm.png`,
      fullPage: true,
    });
  });

  test("calendar page - week view navigated to next week", async ({ page }) => {
    await page.goto("/calendar");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Click "Next week" button
    await page.getByLabel("Next week").click();
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/14-calendar-next-week.png`,
      fullPage: true,
    });
  });
});
