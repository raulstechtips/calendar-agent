import type { ReactNode } from "react";

/**
 * Lightweight markdown-to-React renderer for chat messages.
 * Handles bold, italic, inline code, numbered lists, and line breaks.
 * No external dependency — the LLM output is simple enough for regex.
 */
export function renderMarkdown(text: string): ReactNode {
  const lines = text.split("\n");
  const elements: ReactNode[] = [];
  let listItems: ReactNode[] = [];

  function flushList() {
    if (listItems.length > 0) {
      elements.push(
        <ol
          key={`ol-${elements.length}`}
          className="list-decimal space-y-0.5 pl-5"
        >
          {listItems}
        </ol>,
      );
      listItems = [];
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!;
    const listMatch = line.match(/^\d+\.\s+(.*)/);

    if (listMatch) {
      listItems.push(<li key={`li-${i}`}>{formatInline(listMatch[1]!)}</li>);
    } else {
      flushList();
      if (line.trim() === "") {
        elements.push(<br key={`br-${i}`} />);
      } else {
        if (elements.length > 0) {
          elements.push(<br key={`br-${i}`} />);
        }
        elements.push(
          <span key={`line-${i}`}>{formatInline(line)}</span>,
        );
      }
    }
  }
  flushList();

  return <>{elements}</>;
}

const INLINE_PATTERN =
  /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;

function formatInline(text: string): ReactNode {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  // Reset lastIndex for global regex
  INLINE_PATTERN.lastIndex = 0;

  while ((match = INLINE_PATTERN.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (match[2]) {
      parts.push(
        <strong key={match.index} className="font-semibold">
          {match[2]}
        </strong>,
      );
    } else if (match[3]) {
      parts.push(
        <em key={match.index}>{match[3]}</em>,
      );
    } else if (match[4]) {
      parts.push(
        <code
          key={match.index}
          className="rounded bg-muted px-1 py-0.5 font-mono text-xs"
        >
          {match[4]}
        </code>,
      );
    }

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length === 1 ? parts[0] : <>{parts}</>;
}
