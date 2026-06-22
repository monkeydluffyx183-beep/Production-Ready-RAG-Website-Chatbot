"use client";
import { useState } from "react";
import { Globe, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Props = { onReady: (sessionId: string) => void };

export default function IngestForm({ onReady }: Props) {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [msg, setMsg] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!url) return;
    setStatus("loading");
    setMsg("Starting crawl…");
    try {
      const res = await fetch(`${API}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, max_pages: 30 }),
      });
      const job = await res.json();
      // Poll
      let final = job;
      while (final.status === "pending" || final.status === "running") {
        await new Promise(r => setTimeout(r, 1500));
        const r = await fetch(`${API}/ingest/${job.job_id}`);
        final = await r.json();
        setMsg(`Status: ${final.status} — ${final.pages_indexed} pages, ${final.chunks_created} chunks`);
      }
      if (final.status === "completed") {
        setStatus("done");
        setMsg(`Indexed ${final.pages_indexed} pages / ${final.chunks_created} chunks`);
        onReady(job.job_id);
      } else {
        setStatus("error");
        setMsg(final.error || "Ingest failed");
      }
    } catch (err: any) {
      setStatus("error");
      setMsg(err.message);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <label className="text-sm font-medium text-slate-700">Website URL</label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="https://docs.example.com"
            className="w-full pl-10 pr-3 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={status === "loading"}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
        >
          {status === "loading" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
          Index Site
        </button>
      </div>
      {msg && (
        <div className={`text-sm flex items-center gap-2 ${
          status === "done" ? "text-emerald-700" :
          status === "error" ? "text-red-700" : "text-slate-600"
        }`}>
          {status === "done" && <CheckCircle2 className="w-4 h-4" />}
          {status === "error" && <AlertCircle className="w-4 h-4" />}
          {status === "loading" && <Loader2 className="w-4 h-4 animate-spin" />}
          {msg}
        </div>
      )}
    </form>
  );
}
