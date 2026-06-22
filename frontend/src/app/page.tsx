"use client";
import { useState } from "react";
import IngestForm from "@/components/IngestForm";
import ChatWindow from "@/components/ChatWindow";
import { Sparkles } from "lucide-react";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  return (
    <main className="min-h-screen p-6 md:p-10">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Site Chatbot</h1>
            <p className="text-sm text-slate-500">Ask questions about any website, powered by RAG.</p>
          </div>
        </header>

        <section className="bg-white p-6 rounded-xl border border-slate-200">
          <IngestForm onReady={setSessionId} />
        </section>

        {sessionId && (
          <section>
            <ChatWindow sessionId={sessionId} />
          </section>
        )}
      </div>
    </main>
  );
}
