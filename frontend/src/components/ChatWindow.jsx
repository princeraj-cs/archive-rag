import { ArrowUp, LoaderCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { queryDocs } from "../api/client";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({
  chat,
  onMessagesChange,
  enabledDocumentIds,
}) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const conversationRef = useRef(null);
  const messages = chat.messages;

  useEffect(() => {
    const conversation = conversationRef.current;
    if (conversation) conversation.scrollTop = conversation.scrollHeight;
  }, [messages.length, loading]);

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) return;

    const userMessage = { role: "user", content: trimmedQuestion };
    onMessagesChange([...messages, userMessage]);
    setQuestion("");
    setLoading(true);
    try {
      const history = messages.slice(-8).map(({ role, content }) => ({
        role,
        content,
      }));
      const response = await queryDocs(
        trimmedQuestion,
        history,
        enabledDocumentIds,
      );
      onMessagesChange([
        ...messages,
        userMessage,
        {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } catch (error) {
      onMessagesChange([
        ...messages,
        userMessage,
        { role: "assistant", content: error.message, sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="chat-panel">
      <div className="conversation" ref={conversationRef}>
        {!messages.length && (
          <div className="empty-state">
            <h2>Ask the archive.</h2>
            <p>
              Upload your documents, then ask a focused question. Every answer
              carries its trail back to the source.
            </p>
          </div>
        )}
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
        {loading && (
          <div className="thinking">
            <LoaderCircle size={16} className="spin" /> Searching the archive...
          </div>
        )}
      </div>
      <form className="composer" onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What do you want to find?"
          aria-label="Question"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          aria-label="Ask question"
          title="Ask question"
        >
          <ArrowUp size={18} />
        </button>
      </form>
    </section>
  );
}
