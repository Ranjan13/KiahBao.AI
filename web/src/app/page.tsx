'use client';
import { useState, useRef, useEffect } from 'react';
import Image from 'next/image';

// ─── Types ────────────────────────────────────────────────────────────────────

interface BuyerProfile {
  youngest_buyer_age: number;
  flat_remaining_lease: number;
  average_monthly_income: number;
  is_family: boolean;
  proximity_km: number;
  living_with_parents: boolean;
  citizenship_status: 'SC' | 'PR';
  partner_citizenship: 'SC' | 'PR' | 'none';
  has_parents_in_sg: boolean;
  years_as_pr?: number;
}

interface NewsItem {
  title: string;
  description: string;
  date: string;
  url: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  route?: string;
  timestamp: Date;
}

interface HealthStatus {
  status: string;
  model: string;
  engine_ready: boolean;
}

interface MarketData {
  status: string;
  average_price?: number;
  sample_count?: number;
  transactions?: Array<Record<string, string>>;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000/api';

const ROUTE_COLORS: Record<string, string> = {
  vector:       'rgba(99, 102, 241, 0.7)',   // indigo
  api:          'rgba(16, 185, 129, 0.7)',   // emerald
  hybrid:       'rgba(245, 158, 11, 0.7)',   // amber
  api_location: 'rgba(20, 184, 166, 0.8)',   // teal — @ location fast-path
};

const QUICK_PROMPTS = [
  "How much EHG grant can I get for my BTO lah?",
  "Can I use CPF-OA to pay for resale flat near my parents?",
  "What's the minimum occupation period (MOP) before I can sell?",
  "Can I hack down the wall between living room and bedroom?",
  "How does the lease decay affect my CPF usage ah?",
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function uid(): string {
  return Math.random().toString(36).slice(2, 9);
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD', maximumFractionDigits: 0 }).format(n);
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusPill({ health }: { health: HealthStatus | null }) {
  if (!health) return (
    <span className="status-pill status-checking">
      <span className="pulse-dot" /> Connecting…
    </span>
  );
  return (
    <span className={`status-pill ${health.engine_ready ? 'status-online' : 'status-offline'}`}>
      <span className="pulse-dot" />
      {health.engine_ready ? 'Model Ready' : 'Model Offline'}
    </span>
  );
}

function RouteTag({ route }: { route?: string }) {
  if (!route) return null;
  const color = ROUTE_COLORS[route] ?? 'rgba(148,163,184,0.6)';
  return (
    <span style={{ background: color }} className="route-tag">
      {route.toUpperCase()}
    </span>
  );
}

function ChatBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`bubble-row ${isUser ? 'bubble-row-user' : 'bubble-row-assistant'}`}>
      {!isUser && (
        <div className="avatar avatar-ai">🏡</div>
      )}
      <div className={`bubble ${isUser ? 'bubble-user' : 'bubble-assistant'}`}>
        {!isUser && <RouteTag route={msg.route} />}
        <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{msg.content}</p>
        <span className="bubble-time">
          {msg.timestamp.toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      {isUser && (
        <div className="avatar avatar-user">🧑</div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uid(),
      role: 'assistant',
      content: "Eh hello! 👋 I'm KiahBao.AI (仔包) — your personal HDB housing kaki!\n\nNo need to kiah (fear) navigating all these grants, CPF rules, and renovation permits alone, lah. Ask me anything — in English, Singlish, or even half-half!",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [market, setMarket] = useState<MarketData | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [profile, setProfile] = useState<BuyerProfile>({
    youngest_buyer_age: 30,
    flat_remaining_lease: 70,
    average_monthly_income: 5000,
    is_family: true,
    proximity_km: 2.5,
    living_with_parents: false,
    citizenship_status: 'SC',
    partner_citizenship: 'none',
    has_parents_in_sg: true,
    years_as_pr: 3,
  });
  const [showProfile, setShowProfile] = useState(false);
  const [profileDirty, setProfileDirty] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ── Lifecycle ──
  useEffect(() => {
    fetchHealth();
    fetchMarket();
    fetchNews();
    const healthInterval = setInterval(fetchHealth, 30_000);
    return () => clearInterval(healthInterval);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── API Calls ──
  async function fetchHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data: HealthStatus = await res.json();
      setHealth(data);
    } catch {
      setHealth({ status: 'error', model: 'unavailable', engine_ready: false });
    }
  }

  async function fetchMarket() {
    try {
      const res = await fetch(`${API_BASE}/market`);
      const data: MarketData = await res.json();
      setMarket(data);
    } catch {
      setMarket(null);
    }
  }

  async function fetchNews() {
    try {
      setNewsLoading(true);
      const res = await fetch(`${API_BASE}/news`);
      const data = await res.json();
      if (data && data.articles) {
        setNews(data.articles);
      }
    } catch (err) {
      console.error("Failed to fetch news:", err);
    } finally {
      setNewsLoading(false);
    }
  }

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return;
    setInput('');

    const userMsg: Message = { id: uid(), role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text, ...profile }),
      });

      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();

      const aiMsg: Message = {
        id: uid(),
        role: 'assistant',
        content: data.response,
        route: data.route,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      const errMsg: Message = {
        id: uid(),
        role: 'assistant',
        content: `Aiyoh, something went wrong lah! 😅\n\n${err instanceof Error ? err.message : 'Unknown error'}\n\nPlease make sure the KiahBao.AI backend server is running on port 8000.`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  function updateProfile(key: keyof BuyerProfile, value: string | number | boolean) {
    setProfile(prev => ({ ...prev, [key]: value }));
    setProfileDirty(true);
  }

  return (
    <div className="app-shell">
      {/* ── Glassmorphic Background ── */}
      <div className="bg-orb bg-orb-1" />
      <div className="bg-orb bg-orb-2" />
      <div className="bg-orb bg-orb-3" />

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">🏡</span>
          <div>
            <h1 className="sidebar-title">KiahBao.AI</h1>
            <p className="sidebar-subtitle">仔包 · Housing Kaki</p>
          </div>
        </div>

        <StatusPill health={health} />

        {/* Market Snapshot Card */}
        <div className="glass-card mt-4">
          <p className="card-label">HDB Market Snapshot</p>
          {market?.average_price ? (
            <>
              <p className="card-price">{formatPrice(market.average_price)}</p>
              <p className="card-sub">avg from {market.sample_count} recent txns</p>
            </>
          ) : (
            <p className="card-sub">Loading market data…</p>
          )}
        </div>

        {/* Model Info Card */}
        {health && (
          <div className="glass-card mt-3">
            <p className="card-label">Local Model</p>
            <p className="card-model">{health.model}</p>
          </div>
        )}

        {/* Latest HDB Pulse News Feed */}
        <div className="glass-card mt-3 news-card-container">
          <p className="card-label mb-2">📰 Latest HDB Pulse</p>
          {newsLoading ? (
            <p className="card-sub">Fetching news updates…</p>
          ) : news.length > 0 ? (
            <div className="news-feed-list">
              {news.map((item, index) => (
                <a
                  key={index}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="news-item-card"
                  title={item.description}
                >
                  <p className="news-item-title">{item.title}</p>
                  <div className="news-item-footer">
                    <span className="news-item-date">{item.date}</span>
                    <span className="news-item-link-icon">↗</span>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <p className="card-sub">No news updates available.</p>
          )}
        </div>

        {/* Quick Prompts */}
        <div className="mt-4">
          <p className="card-label mb-2">Quick Ask</p>
          {QUICK_PROMPTS.map((q, i) => (
            <button
              key={i}
              className="quick-prompt-btn"
              onClick={() => sendMessage(q)}
              disabled={loading}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Buyer Profile Toggle */}
        <button
          className={`profile-toggle-btn mt-auto ${profileDirty ? 'profile-dirty' : ''}`}
          onClick={() => setShowProfile(v => !v)}
        >
          {showProfile ? '▲ Hide Profile' : '▼ My Buyer Profile'}
          {profileDirty && <span className="dirty-dot" />}
        </button>
      </aside>

      {/* ── Main Panel ── */}
      <main className="main-panel">
        {/* Profile Editor (collapsible) */}
        {showProfile && (
          <div className="profile-editor glass-card">
            <h2 className="profile-title">Your Buyer Profile</h2>
            <p className="profile-hint">These fields personalise grant calculations. All data stays local.</p>
            <div className="profile-grid">
              {/* ── Citizenship Section ── */}
              <div className="profile-section-label">Citizenship</div>
              <label className="profile-field">
                <span>Your Citizenship</span>
                <select
                  value={profile.citizenship_status}
                  onChange={e => updateProfile('citizenship_status', e.target.value as 'SC' | 'PR')}
                >
                  <option value="SC">🇸🇬 Singapore Citizen (SC)</option>
                  <option value="PR">🟢 Permanent Resident (PR)</option>
                </select>
              </label>
              <label className="profile-field">
                <span>Partner / Spouse Citizenship</span>
                <select
                  value={profile.partner_citizenship}
                  onChange={e => updateProfile('partner_citizenship', e.target.value as 'SC' | 'PR' | 'none')}
                >
                  <option value="none">Single / Not applicable</option>
                  <option value="SC">🇸🇬 Singapore Citizen (SC)</option>
                  <option value="PR">🟢 Permanent Resident (PR)</option>
                </select>
              </label>
              
              {profile.citizenship_status === 'PR' && (
                <label className="profile-field">
                  <span>Years as PR (dur. status)</span>
                  <input
                    type="number" min={0} max={50}
                    value={profile.years_as_pr ?? 3}
                    onChange={e => updateProfile('years_as_pr', Number(e.target.value))}
                  />
                </label>
              )}

              <label className="profile-field profile-field-checkbox">
                <input
                  type="checkbox" checked={profile.has_parents_in_sg}
                  onChange={e => updateProfile('has_parents_in_sg', e.target.checked)}
                />
                <span>Parents / Children are Singapore-based <span className="hint-text">(for PHG eligibility)</span></span>
              </label>

              {/* Comprehensive dynamic notice based on citizenship combination */}
              <div className="pr-notice">
                {profile.citizenship_status === 'PR' ? (
                  profile.partner_citizenship === 'SC' ? (
                    <span>🇸🇬 <strong>SC+PR Family Path:</strong> Eligible for CPF Housing Grant (resale only, up to $40,000) and Proximity Housing Grant (PHG) if living near/with parents in SG. No EHG eligibility.</span>
                  ) : profile.partner_citizenship === 'PR' ? (
                    <span>🟢 <strong>PR+PR Family Path:</strong> Eligible to buy a resale HDB flat if both are PRs for ≥ 3 years. <strong>Note:</strong> Pure SPR families are eligible for up to $20,000 CPF housing grant but not EHG or PHG.</span>
                  ) : (
                    <span>⚠️ <strong>Single PR Path:</strong> Single PRs are <strong>not eligible</strong> to purchase HDB flats under any scheme. You must apply with a citizen spouse or form a PR family.</span>
                  )
                ) : (
                  profile.partner_citizenship === 'PR' ? (
                    <span>🇸🇬 <strong>SC+PR Family Path:</strong> Eligible for CPF Housing Grant (resale only, up to $40,000) and Proximity Housing Grant (PHG) if parents are in SG.</span>
                  ) : (
                    <span>🇸🇬 <strong>Pure SC Path:</strong> Full eligibility for Enhanced CPF Housing Grant (EHG - up to $120,000) and Proximity Housing Grant (PHG - up to $30,000).</span>
                  )
                )}
                {!profile.has_parents_in_sg && (
                  <span className="block mt-1 font-semibold text-amber-400">
                    <br />⚠️ PHG Not Applicable: Since parents/family are not Singapore-based, you will not receive any Proximity Housing Grant (PHG).
                  </span>
                )}
                {profile.citizenship_status === 'PR' && profile.partner_citizenship === 'PR' && profile.years_as_pr !== undefined && profile.years_as_pr < 3 && (
                  <span className="block mt-1 font-semibold text-rose-400">
                    <br />❌ Ineligible: SPR buyers must both hold PR status for ≥ 3 years before buying HDB (current setting: {profile.years_as_pr} years).
                  </span>
                )}
              </div>
              {/* ── Housing Profile Section ── */}
              <div className="profile-section-label">Housing Profile</div>
              <label className="profile-field">
                <span>Youngest Buyer Age</span>
                <input
                  type="number" min={21} max={99}
                  value={profile.youngest_buyer_age}
                  onChange={e => updateProfile('youngest_buyer_age', Number(e.target.value))}
                />
              </label>
              <label className="profile-field">
                <span>Flat Remaining Lease (yrs)</span>
                <input
                  type="number" min={1} max={99}
                  value={profile.flat_remaining_lease}
                  onChange={e => updateProfile('flat_remaining_lease', Number(e.target.value))}
                />
              </label>
              <label className="profile-field">
                <span>Monthly Household Income (SGD)</span>
                <input
                  type="number" min={0} step={100}
                  value={profile.average_monthly_income}
                  onChange={e => updateProfile('average_monthly_income', Number(e.target.value))}
                />
              </label>
              <label className="profile-field">
                <span>Distance from Parents (km)</span>
                <input
                  type="number" min={0} step={0.1}
                  value={profile.proximity_km}
                  onChange={e => updateProfile('proximity_km', Number(e.target.value))}
                />
              </label>
              <label className="profile-field profile-field-checkbox">
                <input
                  type="checkbox" checked={profile.is_family}
                  onChange={e => updateProfile('is_family', e.target.checked)}
                />
                <span>Family / Married Couple Application</span>
              </label>
              <label className="profile-field profile-field-checkbox">
                <input
                  type="checkbox" checked={profile.living_with_parents}
                  onChange={e => updateProfile('living_with_parents', e.target.checked)}
                />
                <span>Living Together with Parents</span>
              </label>
            </div>
            <button className="btn-save" onClick={() => { setShowProfile(false); setProfileDirty(false); }}>
              ✓ Save Profile
            </button>
          </div>
        )}

        {/* Chat Area */}
        <div className="chat-area">
          {messages.map(msg => (
            <ChatBubble key={msg.id} msg={msg} />
          ))}

          {loading && (
            <div className="bubble-row bubble-row-assistant">
              <div className="avatar avatar-ai">🏡</div>
              <div className="bubble bubble-assistant bubble-loading">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input Bar */}
        <div className="input-bar">
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              className="chat-input"
              placeholder="Ask about HDB grants, CPF, renovation rules… or type @Tampines for live prices!"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <div className="input-hints">
              <span className="hint-chip" onClick={() => setInput(v => v + '@')} title="Type @TownName for live prices">
                @ location
              </span>
            </div>
          </div>
          <button
            className="send-btn"
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
            aria-label="Send message"
          >
            {loading ? (
              <svg className="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            )}
          </button>
        </div>
        <p className="disclaimer">KiahBao.AI provides general housing guidance only — always verify with HDB and CPF Board directly.</p>
      </main>
    </div>
  );
}
