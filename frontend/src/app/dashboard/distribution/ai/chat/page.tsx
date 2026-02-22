'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import { Brain, Send, RefreshCw, Sparkles, MessageSquare, TrendingUp, Users, AlertTriangle, Target, BarChart3, IndianRupee, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { dmsAiApi } from '@/lib/api';

// ─── Types ─────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  intent?: string;
  timestamp: Date;
  data?: unknown[];
}

interface SuggestionGroup {
  label: string;
  icon: React.ElementType;
  questions: string[];
}

// ─── Suggestion Groups ───────────────────────────────────────────────────────

const SUGGESTIONS: SuggestionGroup[] = [
  {
    label: 'Performance',
    icon: Users,
    questions: [
      'Which dealers are underperforming?',
      'Who are the top performing dealers?',
    ],
  },
  {
    label: 'Demand',
    icon: TrendingUp,
    questions: [
      "What's next month's demand forecast?",
      'Which dealers haven\'t ordered recently?',
    ],
  },
  {
    label: 'Collections',
    icon: IndianRupee,
    questions: [
      "What's our outstanding collection?",
      'Show me overdue dealers by aging bucket',
    ],
  },
  {
    label: 'Schemes',
    icon: Target,
    questions: [
      'How are our dealer schemes performing?',
      'Which schemes should we retire or extend?',
    ],
  },
  {
    label: 'Alerts',
    icon: AlertTriangle,
    questions: [
      'What alerts need immediate attention?',
      'Give me a full DMS status overview',
    ],
  },
];

const intentColors: Record<string, string> = {
  dealer_performance: 'bg-blue-100 text-blue-700',
  demand_forecast: 'bg-green-100 text-green-700',
  inactive_dealers: 'bg-orange-100 text-orange-700',
  collection_status: 'bg-red-100 text-red-700',
  scheme_effectiveness: 'bg-purple-100 text-purple-700',
  top_dealers: 'bg-yellow-100 text-yellow-700',
  alerts: 'bg-pink-100 text-pink-700',
  help: 'bg-gray-100 text-gray-600',
};

const intentLabels: Record<string, string> = {
  dealer_performance: 'Dealer Performance',
  demand_forecast: 'Demand Forecast',
  inactive_dealers: 'Inactive Dealers',
  collection_status: 'Collections',
  scheme_effectiveness: 'Scheme Effectiveness',
  top_dealers: 'Top Dealers',
  alerts: 'Alerts',
  help: 'Help',
};

// ─── Main Page ───────────────────────────────────────────────────────────────

let msgIdCounter = 0;

const WELCOME_MESSAGE: ChatMessage = {
  id: msgIdCounter++,
  role: 'assistant',
  text:
    'Hi! I\'m your DMS AI Assistant. I can analyse your dealer network and answer questions about performance, demand, collections, and schemes.\n\nTry one of the suggestions below, or type your own question.',
  timestamp: new Date(),
};

export default function DMSChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: msgIdCounter++,
      role: 'user',
      text: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const result = await dmsAiApi.chat(text.trim());
      const response = result.response ?? {};
      const assistantMsg: ChatMessage = {
        id: msgIdCounter++,
        role: 'assistant',
        text: response.text ?? 'No response received.',
        intent: result.intent,
        timestamp: new Date(result.timestamp ?? Date.now()),
        data: response.data,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: msgIdCounter++,
          role: 'assistant',
          text: 'Sorry, I encountered an error while processing your query. Please try again.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const clearChat = () => {
    setMessages([WELCOME_MESSAGE]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-4 gap-4">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Brain className="h-6 w-6 text-purple-600" />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">DMS AI Chat</h1>
              <Badge className="bg-purple-100 text-purple-700 border-purple-200">AI</Badge>
            </div>
            <p className="text-xs text-muted-foreground">Ask anything about your dealer network</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={clearChat} className="text-muted-foreground">
          <RefreshCw className="h-4 w-4 mr-1.5" />
          Clear
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center mr-2 mt-0.5">
                <Brain className="h-3.5 w-3.5 text-purple-600" />
              </div>
            )}
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : ''}`}>
              <div
                className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-purple-600 text-white rounded-tr-sm'
                    : 'bg-muted rounded-tl-sm'
                }`}
              >
                {msg.text}
              </div>
              <div className={`flex items-center gap-2 mt-1 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                <span className="text-xs text-muted-foreground">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                {msg.intent && msg.intent !== 'help' && (
                  <span className={`text-xs rounded-full px-2 py-0.5 ${intentColors[msg.intent] ?? 'bg-gray-100 text-gray-600'}`}>
                    {intentLabels[msg.intent] ?? msg.intent}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center mr-2 mt-0.5">
              <Brain className="h-3.5 w-3.5 text-purple-600" />
            </div>
            <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 2 && !loading && (
        <div className="shrink-0 space-y-2">
          <p className="text-xs text-muted-foreground flex items-center gap-1.5">
            <Sparkles className="h-3 w-3" />
            Quick questions
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.flatMap((g) =>
              g.questions.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-xs rounded-full border bg-background px-3 py-1.5 hover:bg-muted transition-colors text-left"
                >
                  {q}
                </button>
              ))
            )}
          </div>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="shrink-0">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(input);
                }
              }}
              placeholder="Ask about dealers, demand, collections, or schemes…"
              rows={1}
              className="w-full resize-none rounded-xl border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
              disabled={loading}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={!input.trim() || loading}
            className="h-12 w-12 rounded-xl bg-purple-600 hover:bg-purple-700 shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-1.5 text-center">
          Press Enter to send · Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}
