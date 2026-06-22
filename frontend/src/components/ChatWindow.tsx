"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import Message, { Source } from "./Message";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Msg = { role: "user" | "assistant"; content: string; sources?: Source[] };

export default function ChatWindow({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", content: q }]);
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, question: q }),
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let sources: Source[] = [];
      let assistantIdx = -1;

      setMessages(m => {
        assistantIdx = m.length;
        return [...m, { role: "assistant", content: "" }];
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventType = line.slice(6).trim();
          else if (line.startsWith("data:")) {
            const data = line.slice(5);
            if (eventType === "sources") {
              sources = JSON.parse(data);
            } else if (eventType === "token") {
              setMessages(m => m.map((msg, i) =>
                i === assistantIdx ? { ...msg, content: msg.content + data } : msg
              ));
            }
          }
        }
      }

      setMessages(m => m.map((msg, i) =>
        i === assistantIdx ? { ...msg, sources } : msg
      ));
    } catch (err: any) {
      setMessages(m => [...m, { role: "assistant", content: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  const suggestions = [
    "What is this site about?",
    "Summarize the main features.",
    "How do I get started?",
  ];

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 mt-12">
            <p className="mb-4">Ask anything about the indexed site</p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map(s => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 rounded-full"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} sources={m.sources} />
        ))}
        <div ref={endRef} />
      </div>
      <form onSubmit={send} className="border-t border-slate-200 p-4 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  );
}
