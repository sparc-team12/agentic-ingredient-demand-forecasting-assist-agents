// `/chat-agent` route (ACRI-45 explanation-on-demand, ACRI-49..52 what-if
// scenarios) — protected by `RequireAuth` in `App.tsx`. Two entry points
// share this single screen (REQ-036 — one Chat Agent interface, not two
// disconnected inputs):
//
// (a) `?ingredientId=123` — wired from "Ask why flagged" in Ingredient
//     Detail's stockout/spoilage risk blocks — auto-sends a pre-filled
//     "Why is this flagged?" first message.
// (b) plain `/chat-agent` (reachable from the top nav) — a free what-if
//     conversation, no ingredient pre-selected.
//
// A single scrollable message list (user messages right-aligned, agent
// replies plain) plus a text input + send button, a "Thinking…" indicator
// while `POST /chat-agent/ask` is in flight (REQ-033's "a few seconds"
// budget), and a plain, non-crashing error message on failure (503
// not-configured, or a network failure) — handled here directly, not only
// relying on the app's top-level error boundary.
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "@/lib/api-client";
import { askChatAgent } from "@/lib/chat-agent-api";

interface ChatMessage {
  id: number;
  role: "user" | "agent";
  text: string;
}

let nextMessageId = 0;

function nextId(): number {
  nextMessageId += 1;
  return nextMessageId;
}

function parseIngredientId(raw: string | null): number | null {
  if (raw === null) return null;
  const parsed = Number(raw);
  return Number.isInteger(parsed) ? parsed : null;
}

export default function ChatAgentRoute() {
  const [searchParams] = useSearchParams();
  const ingredientId = parseIngredientId(searchParams.get("ingredientId"));

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const autoSentForIngredientRef = useRef<number | null>(null);

  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (trimmed === "") return;

      setMessages((prev) => [...prev, { id: nextId(), role: "user", text: trimmed }]);
      setError(null);
      setSending(true);

      askChatAgent({ message: trimmed, ingredient_id: ingredientId })
        .then((response) => {
          setMessages((prev) => [...prev, { id: nextId(), role: "agent", text: response.reply }]);
        })
        .catch((err: unknown) => {
          setError(
            err instanceof ApiError
              ? err.detail
              : "Could not reach the Chat Agent. Check your connection and try again.",
          );
        })
        .finally(() => {
          setSending(false);
        });
    },
    [ingredientId],
  );

  useEffect(() => {
    if (ingredientId === null) return;
    if (autoSentForIngredientRef.current === ingredientId) return;
    autoSentForIngredientRef.current = ingredientId;
    sendMessage("Why is this flagged?");
  }, [ingredientId, sendMessage]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sending) return;
    const text = draft;
    setDraft("");
    sendMessage(text);
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Chat Agent</h1>
        <p className="page__subtitle">
          Ask why an ingredient is flagged, or pose a what-if scenario in plain language.
        </p>
      </div>

      <section className="card chat-agent">
        <div className="chat-agent__messages" role="log" aria-live="polite">
          {messages.length === 0 && !sending && (
            <p className="empty-state">
              {ingredientId !== null
                ? "Loading this ingredient's explanation…"
                : 'Try something like "what if we sell 20 more butter chicken next Saturday?"'}
            </p>
          )}
          {messages.map((message) => (
            <p
              key={message.id}
              className={`chat-agent__message chat-agent__message--${message.role}`}
            >
              {message.text}
            </p>
          ))}
          {sending && <p className="hint-text">Thinking…</p>}
        </div>

        {error !== null && (
          <p role="alert" className="alert">
            {error}
          </p>
        )}

        <form className="chat-agent__composer" onSubmit={handleSubmit} aria-label="Send a message">
          <input
            type="text"
            aria-label="Message"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            disabled={sending}
            placeholder="Type a message…"
            autoComplete="off"
          />
          <button
            type="submit"
            className="btn btn--primary"
            disabled={sending || draft.trim() === ""}
          >
            Send
          </button>
        </form>
      </section>
    </main>
  );
}
