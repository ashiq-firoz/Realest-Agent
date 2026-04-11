'use client';

import { useState, useRef, useEffect, CSSProperties } from 'react';
import { Send, Sparkles, Minimize2, Maximize2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message { role: 'user' | 'assistant'; content: string; }

const SUGGESTIONS = [
  'Growth potential in Parramatta?',
  'Duplex feasibility for $900k',
  'Top 5 suburbs near Brisbane',
  'Rental yield in Geelong?',
];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: "G'day! I'm your Aussie Real Estate AI Agent. Ask me about suburb growth, development feasibility, rental yields, or portfolio strategy.",
  }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sendRef = useRef<((text: string) => Promise<void>) | null>(null);

  useEffect(() => {
    if (scrollRef.current && !minimized) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading, minimized]);

  useEffect(() => {
    const handleAskAgent = (e: any) => {
      const query = e.detail?.query;
      if (query && sendRef.current) {
        setMinimized(false);
        sendRef.current(query);
      }
    };
    window.addEventListener('ASK_AGENT', handleAskAgent as any);
    return () => window.removeEventListener('ASK_AGENT', handleAskAgent as any);
  }, []);

  const send = async (text: string) => {
    const msg = text.trim();
    if (!msg || isLoading) return;
    setInput('');
    setMessages(p => [...p, { role: 'user', content: msg }]);
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      
      let replyText = data.reply;
      if (!replyText && data.detail) {
        replyText = `⚠️ Error: ${typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)}`;
      }
      
      if (typeof replyText === 'object' && replyText !== null) {
        if (Array.isArray(replyText)) {
          replyText = replyText.map((i: any) => i.text || JSON.stringify(i)).join('\n');
        } else {
          replyText = replyText.text || JSON.stringify(replyText);
        }
      }
      
      setMessages(p => [...p, { role: 'assistant', content: replyText || 'No response from agent.' }]);
    } catch {
      setMessages(p => [...p, { role: 'assistant', content: '⚠️ Backend offline. Start the server on port 8000.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    sendRef.current = send;
  }, [send]);

  return (
    <motion.div 
      initial={false}
      animate={{ height: minimized ? 70 : '100%' }}
      transition={{ type: 'spring', stiffness: 200, damping: 25 }}
      style={{ ...PANEL_STYLE, justifyContent: minimized ? 'center' : 'flex-start' }}
    >
      {/* Header */}
      <div style={{ ...HEADER_STYLE, borderBottom: minimized ? 'none' : '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={AVATAR_STYLE}>
              <Sparkles size={14} color="white" />
            </div>
            <div>
              <div className="font-display" style={{ fontSize: 13, fontWeight: 800, color: 'var(--text)' }}>AI Negotiator</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span className="blink" style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', display: 'inline-block', boxShadow: '0 0 8px #10b981' }} />
                <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>Gemini Flash Active</span>
              </div>
            </div>
          </div>
          <button 
            onClick={() => setMinimized(!minimized)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: 8, borderRadius: 8, transition: 'background 0.2s' }}
            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          >
            {minimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {!minimized && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}
          >
            {/* Messages */}
            <div ref={scrollRef} style={MESSAGES_STYLE}>
              {messages.length === 1 && (
                <div style={{ padding: '4px 0 12px' }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Quick actions</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {SUGGESTIONS.map(s => (
                      <button key={s} onClick={() => send(s)} style={CHIP_STYLE}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200, damping: 20 }}
                    style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 10 }}
                  >
                    <div
                      className={msg.role === 'user' ? 'bubble-user' : 'bubble-ai'}
                      style={{
                        maxWidth: '88%',
                        padding: '12px 16px',
                        fontSize: 13.5,
                        lineHeight: 1.6,
                        color: msg.role === 'user' ? '#fff' : 'var(--text)',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {msg.content}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {isLoading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', marginBottom: 8 }}>
                  <div className="bubble-ai" style={{ padding: '14px 18px', display: 'flex', gap: 6, alignItems: 'center' }}>
                    {[0, 0.2, 0.4].map(d => (
                      <span key={d} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--primary-light)', display: 'block', animation: `blink 1.2s ease ${d}s infinite` }} />
                    ))}
                  </div>
                </motion.div>
              )}
            </div>

            {/* Input */}
            <div style={INPUT_AREA_STYLE}>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && send(input)}
                  placeholder="Ask about any suburb or deal..."
                  style={INPUT_STYLE}
                />
                <button
                  onClick={() => send(input)}
                  disabled={isLoading || !input.trim()}
                  style={SEND_BTN_STYLE}
                >
                  <Send size={16} strokeWidth={2.5} />
                </button>
              </div>
              <p style={{ textAlign: 'center', fontSize: 10, color: 'var(--text-dim)', marginTop: 10, letterSpacing: '0.05em' }}>
                Powered by Gemini 3 Flash Preview · AU CoreLogic + ABS Data
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ─── Styles ─── */
const PANEL_STYLE: CSSProperties = {
  display: 'flex', flexDirection: 'column',
  height: '100%', overflow: 'hidden',
  background: 'rgba(7, 7, 14, 0.88)',
  backdropFilter: 'blur(32px)',
  WebkitBackdropFilter: 'blur(32px)',
  border: '1px solid var(--border-hi)',
  borderRadius: 24,
};

const HEADER_STYLE: CSSProperties = {
  padding: '14px 18px',
  borderBottom: '1px solid var(--border)',
  background: 'rgba(255,255,255,0.02)',
  flexShrink: 0,
};

const AVATAR_STYLE: CSSProperties = {
  width: 34, height: 34, borderRadius: 10,
  background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  flexShrink: 0,
  boxShadow: '0 0 16px rgba(124, 58, 237, 0.3)',
};

const MESSAGES_STYLE: CSSProperties = {
  flex: 1, overflowY: 'auto',
  padding: '16px 16px 8px',
  display: 'flex', flexDirection: 'column',
  gap: 0,
};

const CHIP_STYLE: CSSProperties = {
  padding: '5px 12px',
  borderRadius: 99,
  border: '1px solid var(--border-hi)',
  background: 'rgba(255,255,255,0.04)',
  color: 'var(--text-muted)',
  fontSize: 11, fontWeight: 500,
  cursor: 'pointer',
  transition: 'all 0.2s',
  whiteSpace: 'nowrap',
};

const INPUT_AREA_STYLE: CSSProperties = {
  padding: '14px 16px',
  borderTop: '1px solid var(--border)',
  background: 'rgba(0,0,0,0.3)',
  flexShrink: 0,
};

const INPUT_STYLE: CSSProperties = {
  width: '100%', paddingRight: 48,
  padding: '12px 52px 12px 16px',
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid var(--border-hi)',
  borderRadius: 16,
  fontSize: 13, fontFamily: 'inherit',
  outline: 'none', color: 'var(--text)',
  transition: 'border-color 0.2s, background 0.2s',
};

const SEND_BTN_STYLE: CSSProperties = {
  position: 'absolute', right: 8,
  width: 36, height: 36,
  borderRadius: 12,
  background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
  border: 'none', cursor: 'pointer',
  color: 'white', display: 'flex',
  alignItems: 'center', justifyContent: 'center',
  transition: 'all 0.2s',
  flexShrink: 0,
};
