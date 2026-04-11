'use client';

import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import {
  Map as MapIcon, MessageSquare, Compass, Search
} from 'lucide-react';
import Chat from './Chat';
import Stats from './Stats';
import UserGuide from './UserGuide';
import { CSSProperties, useState, useEffect } from 'react';

const DynamicMap = dynamic(() => import('./Map'), {
  ssr: false,
  loading: () => (
    <div style={{ width: '100%', height: '100%', background: '#05050a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="font-display" style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-dim)', letterSpacing: '0.3em', textTransform: 'uppercase' }}>
        Loading Map…
      </div>
    </div>
  ),
});

const NAV_MAIN = [
  { icon: MapIcon, id: 'map' },
  { icon: MessageSquare, id: 'chat' },
  { icon: Compass, id: 'guide' }
];

export default function Dashboard() {
  const [searchVal, setSearchVal] = useState('');
  const [activeTab, setActiveTab] = useState('map');

  useEffect(() => {
    const handleMapClick = () => setActiveTab('chat');
    window.addEventListener('ASK_AGENT', handleMapClick);
    return () => window.removeEventListener('ASK_AGENT', handleMapClick);
  }, []);

  return (
    <div className="app-shell">
      {/* ── Ambient Glows ── */}
      <div style={GLOW_CONTAINER} aria-hidden>
        <div style={{ ...GLOW, top: '-15%', left: '-10%', background: 'radial-gradient(circle, rgba(37,99,235,0.22) 0%, transparent 70%)', width: '50%', height: '50%' }} />
        <div style={{ ...GLOW, bottom: '-10%', right: '-5%',  background: 'radial-gradient(circle, rgba(124,58,237,0.16) 0%, transparent 70%)', width: '40%', height: '40%' }} />
      </div>

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <motion.div
          whileHover={{ scale: 1.08, rotate: 4 }}
          whileTap={{ scale: 0.95 }}
          style={LOGO_STYLE}
        >
          <span className="font-display" style={{ fontSize: 18, fontWeight: 900, color: '#fff', fontStyle: 'italic' }}>R</span>
        </motion.div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, marginTop: 28, padding: '0 10px', width: '100%' }}>
          {NAV_MAIN.map((item) => (
            <NavBtn key={item.id} icon={item.icon} active={activeTab === item.id} onClick={() => setActiveTab(item.id)} />
          ))}
        </nav>
      </aside>

      {/* ── Main ── */}
      <div className="main-area">
        {/* Map behind everything */}
        <div className="map-backdrop">
          <DynamicMap />
          <div className="map-vignette" />
        </div>

        {/* Left panel — the side drawer */}
        <div className="left-panel">
          {/* Branding */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 }}
            style={BRAND_CARD}
          >
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
              <span className="badge badge-blue">Enterprise AI</span>
              <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-dim)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>AU Market</span>
            </div>
            <h1 className="font-display text-gradient" style={{ fontSize: 28, fontWeight: 900, marginBottom: 4 }}>
              REALAGENT.AI
            </h1>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500, letterSpacing: '0.02em' }}>
              Advanced Property Intelligence & Prediction Engine
            </p>
          </motion.div>

          {['map', 'chat'].includes(activeTab) && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
              <Stats />
            </motion.div>
          )}

          {activeTab === 'guide' && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ flex: 1, minHeight: 0 }}
            >
              <UserGuide />
            </motion.div>
          )}
        </div>

        {/* ── MAP HUD overlays ── */}
        <div className="map-hud" style={{ pointerEvents: 'none' }}>
          {/* Search bar — top center */}
          <div style={{ position: 'absolute', top: 20, left: '50%', transform: 'translateX(-50%)', width: 'min(640px, calc(100% - 300px))', pointerEvents: 'auto', zIndex: 10 }}>
            <div className="surface-dark" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 18px', borderRadius: 18, boxShadow: '0 10px 40px rgba(0,0,0,0.5)' }}>
              <Search size={18} color="var(--primary-light)" strokeWidth={2.5} />
              <input
                value={searchVal}
                onChange={e => setSearchVal(e.target.value)}
                placeholder="Search suburb, postcode or property..."
                style={{ flex: 1, background: 'transparent', border: 'none', fontSize: 13, fontFamily: 'inherit', outline: 'none' }}
              />
              <div style={KBD_STYLE}>⌘K</div>
            </div>
          </div>

          {/* Centered Chat HUD */}
          <div style={{ position: 'absolute', top: 90, bottom: 24, left: '50%', transform: 'translateX(-50%)', width: 'min(700px, 90vw)', pointerEvents: 'auto', display: activeTab === 'chat' ? 'flex' : 'none', flexDirection: 'column', zIndex: 20 }}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(0,0,0,0.6)', borderRadius: 24 }}
            >
              <Chat />
            </motion.div>
          </div>

          {/* Legend — bottom right */}
          <div style={{ position: 'absolute', bottom: 24, right: 24, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10, pointerEvents: 'auto' }}>
            <div className="surface-dark" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '10px 20px', borderRadius: 16 }}>
              <LegendDot color="#10b981" label="Growth Max" />
              <LegendDot color="#3b82f6" label="Yield Focus" />
              <LegendDot color="#f59e0b" label="Refi Ready" />
            </div>
            <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-dim)', letterSpacing: '0.25em', textTransform: 'uppercase', padding: '4px 12px', background: 'rgba(0,0,0,0.5)', borderRadius: 99, border: '1px solid var(--border)' }}>
              SYS ● STABLE
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Sub-components ─────────────────────────────────── */
function NavBtn({ icon: Icon, active = false, onClick }: { icon: React.ElementType; active?: boolean; onClick?: () => void }) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.92 }}
      style={{
        width: '100%', padding: '10px 0',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        borderRadius: 14, border: 'none', cursor: 'pointer',
        background: active ? 'rgba(37,99,235,0.12)' : 'transparent',
        color: active ? 'var(--primary-light)' : 'var(--text-dim)',
        transition: 'all 0.2s',
        boxShadow: active ? '0 0 16px rgba(59,130,246,0.12)' : 'none',
      }}
    >
      <Icon size={20} strokeWidth={active ? 2.5 : 2} />
    </motion.button>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, boxShadow: `0 0 10px ${color}` }} />
      <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</span>
    </div>
  );
}

/* ─── Inline styles ─────────────────────────────────── */
const GLOW_CONTAINER: CSSProperties = {
  position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
};

const GLOW: CSSProperties = {
  position: 'absolute',
  borderRadius: '50%',
  filter: 'blur(80px)',
  willChange: 'opacity',
};

const LOGO_STYLE: CSSProperties = {
  width: 44, height: 44, borderRadius: 14,
  background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  cursor: 'pointer', flexShrink: 0,
  boxShadow: '0 4px 20px rgba(37,99,235,0.3)',
};

const BRAND_CARD: CSSProperties = {
  background: 'rgba(7, 7, 14, 0.82)',
  backdropFilter: 'blur(24px)',
  WebkitBackdropFilter: 'blur(24px)',
  border: '1px solid var(--border-hi)',
  borderLeft: '3px solid var(--primary-light)',
  borderRadius: 20,
  padding: '18px 20px',
  flexShrink: 0,
};

const KBD_STYLE: CSSProperties = {
  fontSize: 10, fontWeight: 700,
  color: 'var(--text-dim)',
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid var(--border)',
  borderRadius: 6,
  padding: '2px 8px',
  letterSpacing: '0.02em',
  whiteSpace: 'nowrap',
};
