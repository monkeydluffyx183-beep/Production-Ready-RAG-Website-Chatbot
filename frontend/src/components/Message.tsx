import ReactMarkdown from "react-markdown";
import { Bot, User, ExternalLink } from "lucide-react";

export type Source = { url: string; title: string; snippet: string; score: number };

type Props = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

export default function Message({ role, content, sources }: Props) {
  const isUser = role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-700"
      }`}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-2`}>
        <div className={`px-4 py-2.5 rounded-2xl ${
          isUser ? "bg-indigo-600 text-white" : "bg-white border border-slate-200"
        }`}>
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
        {sources && sources.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {sources.map((s, i) => (
              <a
                key={i}
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-700 hover:border-indigo-500 hover:text-indigo-700 transition"
                title={s.snippet}
              >
                <ExternalLink className="w-3 h-3" />
                <span className="truncate max-w-[200px]">{s.title || s.url}</span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
