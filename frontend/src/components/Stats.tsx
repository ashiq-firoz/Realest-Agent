'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, Home, Shield, Zap, Info, ChevronDown } from 'lucide-react';

const STATS = [
  { label: 'Growth Prob.', value: '84%',  sub: 'vs 72% last qtr',  icon: TrendingUp, color: '#10b981', glow: 'rgba(16,185,129,0.18)', details: (
      <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color: 'var(--text)' }}>
          <Info size={14} color="var(--primary-light)"/> Justification
        </div>
        <div style={{ borderLeft: '2px solid #10b981', paddingLeft: 10, marginBottom: 10 }}>
          <p><strong>+12%</strong> momentum driven by infrastructure announcements in Western Sydney.</p>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.05)', height: 40, borderRadius: 6, display: 'flex', alignItems: 'flex-end', padding: '4px', gap: '2px' }}>
           <div style={{ width: '20%', height: '40%', background: 'rgba(16,185,129,0.2)' }}></div>
           <div style={{ width: '20%', height: '50%', background: 'rgba(16,185,129,0.4)' }}></div>
           <div style={{ width: '20%', height: '70%', background: 'rgba(16,185,129,0.6)' }}></div>
           <div style={{ width: '20%', height: '84%', background: 'rgba(16,185,129,1)' }}></div>
        </div>
        <div style={{ fontSize: 9, marginTop: 8, textAlign: 'right', opacity: 0.6 }}>Source: CoreLogic Predictive Model</div>
      </div>
  )},
  { label: 'Avg. Yield',   value: '5.2%', sub: 'Inner East Sydney', icon: Home,       color: '#3b82f6', glow: 'rgba(59,130,246,0.18)', details: (
      <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
        <ul style={{ paddingLeft: 16 }}>
          <li>Units: <strong>5.8%</strong></li>
          <li>Houses: <strong>3.4%</strong></li>
        </ul>
        <div style={{ fontSize: 9, marginTop: 8, textAlign: 'right', opacity: 0.6 }}>Source: Domain Data</div>
      </div>
  ) },
  { label: 'Risk Score',   value: 'Low',  sub: 'Macro stable',      icon: Shield,     color: '#f59e0b', glow: 'rgba(245,158,11,0.18)', details: (
      <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
        <p>Interest rates holding steady. Demand outstripping supply by 1.4x in top suburbs.</p>
        <div style={{ fontSize: 9, marginTop: 8, textAlign: 'right', opacity: 0.6 }}>Source: RBA & ABS Data</div>
      </div>
  ) },
  { label: 'Hot Suburbs',  value: '14',   sub: 'Updated today',     icon: Zap,        color: '#a78bfa', glow: 'rgba(167,139,250,0.18)', details: (
      <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {['Surry Hills', 'Bondi Beach', 'Parramatta', 'Manly', 'Newtown'].map(s => (
            <span key={s} style={{ background: 'rgba(167,139,250,0.2)', color: '#c4b5fd', padding: '2px 8px', borderRadius: 99, fontSize: 10 }}>{s}</span>
          ))}
          <span style={{ fontSize: 10, padding: '2px 4px' }}>+ 9 more</span>
        </div>
      </div>
  ) },
];

export default function Stats() {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const toggle = (i: number) => {
    setExpandedIndex(expandedIndex === i ? null : i);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            onClick={() => toggle(i)}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, type: 'spring', stiffness: 180 }}
            className="surface stat-card"
            style={{ borderRadius: 18, cursor: 'pointer', overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: 34, height: 34,
                borderRadius: 10,
                background: s.glow,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: 10,
                border: `1px solid ${s.color}33`,
              }}>
                <s.icon size={16} color={s.color} strokeWidth={2.5} />
              </div>
              <ChevronDown size={14} color="var(--text-dim)" style={{ transform: expandedIndex === i ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }} />
            </div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
              {s.label}
            </div>
            <div className="font-display" style={{ fontSize: 22, fontWeight: 900, color: 'var(--text)', lineHeight: 1, marginBottom: 5 }}>
              {s.value}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', fontWeight: 500 }}>{s.sub}</div>

            <AnimatePresence>
              {expandedIndex === i && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div style={{ paddingTop: 8, borderTop: '1px solid var(--border)', marginTop: 12 }}>
                    {s.details}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
