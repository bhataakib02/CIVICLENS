'use client';

import React, { useState, useRef, useEffect } from 'react';
import { askAssistant } from '@/lib/api/assistant';
import { AssistantResponse } from '@/types/api';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert } from '@/components/ui/alert';
import { StatusBadge } from '@/components/ui/status-badge';
import { Bot, User, Send, BookOpen, ShieldAlert, Sparkles } from 'lucide-react';
import Link from 'next/link';

interface MessageItem {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: AssistantResponse['citations'];
  eligibilityCalls?: AssistantResponse['eligibility_tool_calls'];
  timestamp: Date;
}

export function AssistantView() {
  const { t } = useTranslation();
  const [inputMessage, setInputMessage] = useState('');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'init',
      sender: 'assistant',
      text: 'Hello! I am CivicLens Assistant. I can help you discover schemes, understand eligibility rules, and guide you through document requirements. How can I help you today?',
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
    scrollToBottom();
  }, [messages, isLoading]);

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
    <div className="space-y-4 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 flex items-center gap-2">
          <Bot className="w-7 h-7 text-blue-600" />
          {t.assistant.title}
        </h1>
        <p className="text-xs text-slate-500 mt-1">{t.assistant.subtitle}</p>
      </div>

      {/* Safety Disclaimer Banner */}
      <Alert type="info" className="bg-blue-50 border-blue-200">
        <div className="flex items-center gap-2 font-medium text-xs">
          <ShieldAlert className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <span>{t.assistant.disclaimer}</span>
        </div>
      </Alert>

      {/* Chat Messages Box */}
      <Card className="h-[520px] flex flex-col justify-between p-0 overflow-hidden border border-slate-200 shadow-sm">
        <CardContent className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-white font-bold text-xs ${
                  msg.sender === 'user' ? 'bg-slate-800' : 'bg-blue-600'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`max-w-[85%] space-y-3 ${msg.sender === 'user' ? 'text-right' : ''}`}>
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-none'
                      : 'bg-slate-100 text-slate-900 rounded-tl-none border border-slate-200/60'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>

                {/* Citations block */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="bg-white p-3 rounded-xl border border-slate-200 text-xs text-slate-700 text-left">
                    <h5 className="font-semibold text-slate-900 flex items-center gap-1 mb-2">
                      <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                      {t.assistant.citations}
                    </h5>
                    <ul className="space-y-1">
                      {msg.citations.map((c, i) => (
                        <li key={i} className="text-slate-600 bg-slate-50 p-2 rounded border border-slate-100">
                          <strong className="text-slate-900">{c.title || 'Official Source'}</strong>
                          {c.section && <span> — Section: {c.section}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Eligibility Tool Call outputs */}
                {msg.eligibilityCalls && msg.eligibilityCalls.length > 0 && (
                  <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-200 text-xs text-left">
                    <h5 className="font-semibold text-emerald-900 flex items-center gap-1 mb-2">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                      {t.assistant.eligibilityChecked}
                    </h5>
                    {msg.eligibilityCalls.map((ec, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-white p-2.5 rounded-lg border border-emerald-100 mb-1">
                        <span className="font-medium text-slate-900">Scheme #{ec.scheme_id.slice(0, 8)}</span>
                        <StatusBadge status={ec.result} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-100 p-4 rounded-2xl text-xs text-slate-500 animate-pulse flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-500 animate-spin" />
                <span>Searching official government knowledge base...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        {/* Input Bar */}
        <div className="p-3 bg-slate-50 border-t border-slate-200">
          {error && <Alert type="error" className="mb-2 text-xs py-1.5">{error}</Alert>}
          <form onSubmit={handleSend} className="flex items-center gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={t.assistant.placeholder}
              className="flex-1 px-4 py-3 bg-white border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <Button type="submit" isLoading={isLoading} className="px-5 py-3">
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
