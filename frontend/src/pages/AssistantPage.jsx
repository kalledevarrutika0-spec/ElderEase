import { useRef, useState } from "react";
import {
  AlertCircle,
  ArrowDownToLine,
  CalendarClock,
  Check,
  Clock3,
  LockKeyhole,
  MessageCircle,
  Send,
  Sparkles,
  Wrench,
} from "lucide-react";
import { api } from "../services/api.js";
import { formatDateTime } from "../utils/format.js";
import { PageHeader, StatusPill } from "../components/UI.jsx";

const EXAMPLE_QUESTION = "Will Grandpa's medicines last for seven days?";

export default function AssistantPage() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const messageListRef = useRef(null);

  async function sendMessage(message = draft) {
    const text = message.trim();
    if (!text || sending) return;
    setDraft("");
    setError("");
    setMessages((current) => [...current, { role: "user", text }]);
    setSending(true);

    try {
      const result = await api.assistantChat(text);
      setMessages((current) => [
        ...current,
        { role: "assistant", text: result.message, tool: result },
      ]);
      requestAnimationFrame(() => {
        messageListRef.current?.scrollTo({
          top: messageListRef.current.scrollHeight,
          behavior: "smooth",
        });
      });
    } catch (requestError) {
      setError(requestError.message || "The assistant request failed.");
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="GEMINI + MCP REFILL WORKFLOW"
        title="Care assistant"
        description="Ask about scheduled medicine stock. Answers use the live refill forecast from Elderease."
      />
      <section className="assistant-shell surface-card">
        <div className="assistant-top">
          <div className="assistant-identity">
            <div className="assistant-avatar"><Sparkles size={20} /></div>
            <div>
              <strong>Elderease assistant</strong>
              <span><i className={sending ? "assistant-status-busy" : ""} />{sending ? "Checking with Gemini + MCP" : "Ready for a refill question"}</span>
            </div>
          </div>
          <div className="assistant-lock"><LockKeyhole size={15} /> API key stays on backend</div>
        </div>

        <div className="assistant-conversation" ref={messageListRef} aria-live="polite">
          {!messages.length && (
            <div className="assistant-welcome">
              <div className="assistant-welcome-icon"><MessageCircle size={23} /></div>
              <h2>Get a clear view of medicine coverage.</h2>
              <p>Gemini answers using the real refill forecast returned by the connected MCP tool. Forecasts are estimates, not medical advice.</p>
              <button
                className="example-question"
                onClick={() => sendMessage(EXAMPLE_QUESTION)}
                disabled={sending}
              >
                <Sparkles size={14} /> “{EXAMPLE_QUESTION}”
              </button>
              <div className="tool-activity">
                <div className="tool-activity-icon"><Wrench size={15} /></div>
                <div><strong>check_refill_status</strong><span>Reads live medicine forecasts through the FastMCP server.</span></div>
                <span className="tool-status">MCP TOOL</span>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <article className={`chat-message chat-${message.role}`} key={`${message.role}-${index}`}>
              <span className={`assistant-message-mark${message.role === "user" ? " user-message-mark" : ""}`}>
                {message.role === "user" ? "Y" : <Sparkles size={14} />}
              </span>
              <div className="chat-message-content">
                <small>{message.role === "user" ? "You" : "Elderease assistant"}</small>
                <div className="assistant-message-bubble">{message.text}</div>
                {message.tool && <ToolResult result={message.tool} />}
              </div>
            </article>
          ))}

          {sending && (
            <div className="tool-running" role="status">
              <span className="assistant-message-mark"><Wrench size={13} /></span>
              <span><i className="assistant-status-busy" /> Calling <strong>check_refill_status</strong>, then asking Gemini to explain its result…</span>
            </div>
          )}
          {error && (
            <div className="assistant-error" role="alert">
              <AlertCircle size={16} /><span>{error}</span>
            </div>
          )}
        </div>

        <form
          className="assistant-composer"
          onSubmit={(event) => {
            event.preventDefault();
            sendMessage();
          }}
        >
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            maxLength={2000}
            disabled={sending}
            aria-label="Ask about medicine refills"
            placeholder="Ask: Will Grandpa's medicines last for seven days?"
          />
          <button type="submit" disabled={sending || !draft.trim()} aria-label="Send message">
            <Send size={17} />
          </button>
        </form>
        <div className="assistant-disclaimer"><LockKeyhole size={13} /> The tool result is shown with Gemini’s explanation. No API credentials are sent to this page.</div>
      </section>
    </>
  );
}

function ToolResult({ result }) {
  const forecasts = result.tool_result?.forecasts || [];

  return (
    <section className="tool-result-card" aria-label={`${result.tool_name} result`}>
      <div className="tool-result-heading">
        <div><Wrench size={14} /><strong>{result.tool_name}</strong><span>completed</span></div>
        <StatusPill tone="success"><Check size={11} /> Real result</StatusPill>
      </div>
      {forecasts.length ? (
        <div className="tool-forecast-list">
          {forecasts.map((forecast) => (
            <article className="tool-forecast-row" key={forecast.medicine_id}>
              <div className="tool-forecast-title">
                <strong>{forecast.medicine_name}</strong>
                {forecast.urgency && <StatusPill tone={forecast.urgency === "CRITICAL" ? "danger" : ["URGENT", "UPCOMING"].includes(forecast.urgency) ? "warning" : "success"}>{forecast.urgency}</StatusPill>}
              </div>
              {forecast.forecast_available ? (
                <div className="tool-forecast-facts">
                  <span><ArrowDownToLine size={13} />{forecast.current_available_stock} units now</span>
                  <span><Clock3 size={13} />{forecast.expected_consumption} expected in 7 days</span>
                  <span><CalendarClock size={13} />Depletion: {formatDateTime(forecast.estimated_depletion_at)}</span>
                </div>
              ) : (
                <p className="tool-forecast-warning">{forecast.data_warnings?.join("; ") || "Forecast unavailable."}</p>
              )}
            </article>
          ))}
        </div>
      ) : (
        <p className="tool-forecast-warning">The MCP tool found no medicine forecasts.</p>
      )}
      <details className="tool-raw-result">
        <summary>View complete tool response</summary>
        <pre>{JSON.stringify(result.tool_result, null, 2)}</pre>
      </details>
      <div className="tool-model-label">Response generated by {result.model}</div>
    </section>
  );
}
