"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";

import {
  fetchCalendarEvents,
  type CalendarEvent,
  type CalendarResult,
} from "@/lib/calendar";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

type CalendarError = "scope_required" | "auth_error" | "api_error";

interface CalendarState {
  events: CalendarEvent[];
  isLoading: boolean;
  error: CalendarError | null;
}

type CalendarAction =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; events: CalendarEvent[] }
  | { type: "FETCH_ERROR"; error: CalendarError };

function calendarReducer(
  state: CalendarState,
  action: CalendarAction,
): CalendarState {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, isLoading: true, error: null };
    case "FETCH_SUCCESS":
      return { events: action.events, isLoading: false, error: null };
    case "FETCH_ERROR":
      return { events: [], isLoading: false, error: action.error };
  }
}

const initialState: CalendarState = {
  events: [],
  isLoading: false,
  error: null,
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

interface UseCalendarEventsReturn {
  events: CalendarEvent[];
  isLoading: boolean;
  error: CalendarError | null;
  refetch: () => void;
}

/** Fetch calendar events directly from the Google Calendar API in the browser. */
export function useCalendarEvents(
  accessToken: string | undefined,
  timeMin: string,
  timeMax: string,
): UseCalendarEventsReturn {
  const [state, dispatch] = useReducer(calendarReducer, initialState);
  const [fetchKey, setFetchKey] = useReducerKey();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!accessToken) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    dispatch({ type: "FETCH_START" });

    fetchCalendarEvents(accessToken, timeMin, timeMax, controller.signal)
      .then((result: CalendarResult) => {
        if (controller.signal.aborted) return;

        if (result.ok) {
          dispatch({ type: "FETCH_SUCCESS", events: result.events });
        } else {
          dispatch({ type: "FETCH_ERROR", error: result.error });
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          dispatch({ type: "FETCH_ERROR", error: "api_error" });
        }
      });

    return () => {
      controller.abort();
    };
  }, [accessToken, timeMin, timeMax, fetchKey]);

  const refetch = useCallback(() => {
    setFetchKey();
  }, [setFetchKey]);

  return { events: state.events, isLoading: state.isLoading, error: state.error, refetch };
}

/** Simple counter hook for triggering refetches. */
function useReducerKey(): [number, () => void] {
  const [key, increment] = useReducer((k: number) => k + 1, 0);
  return [key, increment];
}
