'use client';

import React, { useState, useRef, useEffect } from 'react';
import { askAssistant } from '@/lib/api/assistant';
import { AssistantResponse } from '@/types/api';
import { useTranslation } from '@/lib/i18n';
import { useAuth } from '@/lib/auth/auth-context';
import { Bot, User, Send, BookOpen, ShieldAlert, Sparkles, X, MessageSquare, Minimize2 } from 'lucide-react';
import { StatusBadge } from '@/components/ui/status-badge';

interface MessageItem {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: AssistantResponse['citations'];
  eligibilityCalls?: AssistantResponse['eligibility_tool_calls'];
  timestamp: Date;
}

export function FloatingAssistantWidget() {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'init',
      sender: 'assistant',
      text: 'Hello! I am your CivicLens AI Assistant. Ask me anything about government schemes, eligibility rules, or required documents.',
      timestamp: new Date()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isLoading, isOpen]);

  if (!isAuthenticated) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputMessage.trim();
    if (!query || isLoading) return;

    const userMsg: MessageItem = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const res = await askAssistant(query, conversationId);
      if (res.conversation_id) setConversationId(res.conversation_id);

      const assistantMsg: MessageItem = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: res.answer,
        citations: res.citations,
        eligibilityCalls: res.eligibility_tool_calls,
        timestamp: new Date()
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || 'Failed to generate response from assistant.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Expanded Floating Chat Panel */}
      {isOpen && (
        <div className="w-[90vw] sm:w-96 h-[520px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden mb-4 transition-all duration-300 animate-in fade-in slide-in-from-bottom-5">
          {/* Widget Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-4 text-white flex items-center justify-between shadow-md">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-extrabold text-sm tracking-wide">Ask CivicLens AI</h3>
                <p className="text-[11px] text-blue-100 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> Live Policy Assistant
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors"
              title="Close chat"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
          </div>

          {/* Chat Messages Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs bg-slate-50/50 dark:bg-slate-950/50">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-2.5 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 text-white font-bold text-[10px] ${
                    msg.sender === 'user' ? 'bg-slate-800 dark:bg-slate-700' : 'bg-blue-600'
                  }`}
                >
                  {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                </div>

                <div className={`max-w-[82%] space-y-2 ${msg.sender === 'user' ? 'text-right' : ''}`}>
                  <div
                    className={`p-3 rounded-2xl text-xs leading-relaxed ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-700 rounded-tl-none shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                  </div>

                  {/* Citations block */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="bg-white dark:bg-slate-800 p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-[11px] text-slate-700 dark:text-slate-300 text-left">
                      <h5 className="font-bold text-slate-900 dark:text-white flex items-center gap-1 mb-1">
                        <BookOpen className="w-3 h-3 text-blue-600" /> Source Citation:
                      </h5>
                      {msg.citations.map((c, i) => (
                        <div key={i} className="text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 p-1.5 rounded border border-slate-100 dark:border-slate-800">
                          <strong className="text-slate-900 dark:text-white">{c.title || 'Official Source'}</strong>
                          {c.section && <span> — {c.section}</span>}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Eligibility Tool Call outputs */}
                  {msg.eligibilityCalls && msg.eligibilityCalls.length > 0 && (
                    <div className="bg-emerald-50 dark:bg-emerald-950/60 p-2.5 rounded-xl border border-emerald-200 dark:border-emerald-800 text-[11px] text-left space-y-1">
                      <h5 className="font-bold text-emerald-900 dark:text-emerald-300 flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-emerald-600" /> Eligibility Re-Evaluated:
                      </h5>
                      {msg.eligibilityCalls.map((ec, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-white dark:bg-slate-900 p-1.5 rounded border border-emerald-100 dark:border-emerald-900">
                          <span className="font-medium text-slate-800 dark:text-slate-200">Scheme #{ec.scheme_id.slice(0, 8)}</span>
                          <StatusBadge status={ec.result} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-xl bg-blue-600 text-white flex items-center justify-center">
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-3 rounded-2xl text-xs text-slate-500 flex items-center gap-2 shadow-sm">
                  <Sparkles className="w-3.5 h-3.5 text-blue-500 animate-spin" />
                  <span>Searching government knowledge base...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Footer Input Bar */}
          <div className="p-3 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
            {error && <div className="mb-2 p-2 bg-red-50 text-red-600 rounded-lg text-[11px] font-medium">{error}</div>}
            <form onSubmit={handleSend} className="flex items-center gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask about schemes, rules..."
                className="flex-1 px-3.5 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className="p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl transition-all shadow-md"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Launcher Circular Button (Amazon / Intercom Style) */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="group relative flex items-center gap-2.5 p-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full shadow-2xl transition-all duration-300 hover:scale-105 active:scale-95 border-2 border-white/30"
        title="Ask CivicLens AI Assistant"
      >
        <span className="relative flex items-center justify-center">
          {isOpen ? (
            <X className="w-6 h-6" />
          ) : (
            <>
              <Bot className="w-6 h-6" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 border-2 border-blue-600 rounded-full animate-ping" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 border-2 border-blue-600 rounded-full" />
            </>
          )}
        </span>

        {!isOpen && (
          <span className="hidden sm:inline text-xs font-bold tracking-wide pr-1">
            Ask CivicLens AI
          </span>
        )}
      </button>
    </div>
  );
}
