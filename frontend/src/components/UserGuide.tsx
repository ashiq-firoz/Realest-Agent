'use client';

import { motion } from 'framer-motion';
import { Compass, MessageCircle, Map as MapIcon, Shield, Layers } from 'lucide-react';

export default function UserGuide() {
  const sections = [
    {
      title: 'AI Negotiator Chat',
      desc: 'Talk directly to the enterprise AI. Ask about suburb yields, duplex feasibilities, or current market stats.',
      icon: MessageCircle,
      color: '#3b82f6',
    },
    {
      title: 'Map HUD',
      desc: 'Pan and zoom on the dark-mode OpenStreetMap layer to visually identify high-growth zones and markers.',
      icon: MapIcon,
      color: '#10b981',
    },
    {
      title: 'Feasibility Engine',
      desc: 'Ask the AI to calculate development potential based on lot size and zoning (e.g., R2/R3 standards).',
      icon: Layers,
      color: '#f59e0b',
    },
    {
      title: 'Risk Analysis',
      desc: 'Get automated checks for typical risks including high vacancy rates, poor infrastructure, or legal red flags.',
      icon: Shield,
      color: '#a78bfa',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0 4px', overflowY: 'auto' }}>
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <div style={{ width: 32, height: 32, borderRadius: 10, background: 'rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Compass size={16} color="#3b82f6" />
          </div>
          <h2 className="font-display" style={{ fontSize: 20, fontWeight: 800 }}>User Guide</h2>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>
          Master the REALAGENT.AI platform. Here is how to navigate the proptech tools available to you.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {sections.map((s, i) => (
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            key={i} 
            className="surface-hi" 
            style={{ padding: 16, borderRadius: 16, border: '1px solid var(--border-hi)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <s.icon size={16} color={s.color} />
              <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.02em', color: 'var(--text)' }}>
                {s.title}
              </div>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.5 }}>
              {s.desc}
            </p>
          </motion.div>
        ))}
      </div>

      <div style={{ marginTop: 'auto', paddingTop: 20 }}>
        <div className="surface" style={{ padding: 16, borderRadius: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>
            System Status
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 12, color: '#10b981', fontWeight: 600 }}>
            <span className="blink" style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
            All Modules Online
          </div>
        </div>
      </div>
    </div>
  );
}
