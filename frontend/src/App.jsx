import React, { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import AccountManager from "./components/AccountManager.jsx";
import ChannelSelector from "./components/ChannelSelector.jsx";
import MetricsCards from "./components/MetricsCards.jsx";
import TrendsChart from "./components/TrendsChart.jsx";
import ChannelCards from "./components/ChannelCards.jsx";

const PRESETS = [
  { label: "7d", days: 7 },
  { label: "28d", days: 28 },
  { label: "90d", days: 90 },
  { label: "1y", days: 365 },
];

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export default function App() {
  const [accounts, setAccounts] = useState([]);
  const [channels, setChannels] = useState([]);
  const [selected, setSelected] = useState([]);
  const [activePreset, setActivePreset] = useState(28);
  const [startDate, setStartDate] = useState(daysAgo(28));
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAccounts, setShowAccounts] = useState(false);
  const [view, setView] = useState("cumulative"); // "cumulative" | "individual"

  const loadAccounts = useCallback(async () => {
    try {
      const accs = await api.getAccounts();
      setAccounts(accs);
    } catch {}
  }, []);

  const loadChannels = useCallback(async () => {
    try {
      const chs = await api.getChannels();
      const valid = chs.filter((c) => !c.error);
      setChannels(valid);
      // Auto-select all on first load
      setSelected((prev) => (prev.length === 0 ? valid.map((c) => c.id) : prev));
    } catch {}
  }, []);

  useEffect(() => {
    // Handle OAuth callback
    const params = new URLSearchParams(window.location.search);
    if (params.get("auth") === "success") {
      window.history.replaceState({}, "", "/");
      loadAccounts();
      loadChannels();
    }
    loadAccounts();
    loadChannels();
  }, [loadAccounts, loadChannels]);

  async function fetchDashboard() {
    if (!selected.length) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDashboard(selected, startDate, endDate);
      setDashboard(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function applyPreset(days) {
    setActivePreset(days);
    setStartDate(daysAgo(days));
    setEndDate(new Date().toISOString().slice(0, 10));
  }

  const cumulativeData = dashboard
    ? {
        ...dashboard.cumulative,
        // Show subscriber count from channel info for cumulative
        subscribers: channels
          .filter((c) => selected.includes(c.id))
          .reduce((sum, c) => sum + (c.subscriberCount || 0), 0),
      }
    : null;

  return (
    <div className="min-h-screen bg-yt-dark">
      {/* Header */}
      <header className="border-b border-yt-border sticky top-0 z-40 bg-yt-dark/95 backdrop-blur">
        <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2 mr-2">
            <svg className="w-6 h-6 text-yt-red" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
            </svg>
            <span className="font-bold text-white text-sm hidden sm:block">YT Dashboard</span>
          </div>

          <ChannelSelector channels={channels} selected={selected} onChange={setSelected} />

          {/* Date presets */}
          <div className="flex gap-1">
            {PRESETS.map((p) => (
              <button
                key={p.days}
                onClick={() => applyPreset(p.days)}
                className={`text-xs px-2.5 py-1.5 rounded-lg transition-colors ${
                  activePreset === p.days
                    ? "bg-yt-red text-white"
                    : "bg-yt-card border border-yt-border text-gray-400 hover:text-white"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Custom dates */}
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <input
              type="date"
              value={startDate}
              onChange={(e) => { setStartDate(e.target.value); setActivePreset(null); }}
              className="bg-yt-card border border-yt-border rounded px-2 py-1.5 text-white text-xs"
            />
            <span>–</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => { setEndDate(e.target.value); setActivePreset(null); }}
              className="bg-yt-card border border-yt-border rounded px-2 py-1.5 text-white text-xs"
            />
          </div>

          <button
            onClick={fetchDashboard}
            disabled={loading || !selected.length}
            className="btn-primary text-sm disabled:opacity-50 flex items-center gap-1.5"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Loading…
              </>
            ) : (
              "Fetch Data"
            )}
          </button>

          <button
            onClick={() => setShowAccounts((s) => !s)}
            className="btn-ghost text-sm ml-auto"
          >
            Accounts {accounts.length > 0 && `(${accounts.length})`}
          </button>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-4 py-6 space-y-6">
        {/* Account manager panel */}
        {showAccounts && (
          <AccountManager
            accounts={accounts}
            onRefresh={() => { loadAccounts(); loadChannels(); }}
          />
        )}

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {!dashboard && !loading && (
          <div className="text-center py-20 text-gray-500">
            {accounts.length === 0
              ? 'Open "Accounts" to connect your Google account(s), then fetch data.'
              : selected.length === 0
              ? "Select at least one channel and click Fetch Data."
              : "Select channels and click Fetch Data to load analytics."}
          </div>
        )}

        {dashboard && (
          <>
            {/* View toggle */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 mr-1">View:</span>
              {["cumulative", "individual"].map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
                    view === v
                      ? "bg-yt-card border border-gray-500 text-white"
                      : "text-gray-500 hover:text-white"
                  }`}
                >
                  {v.charAt(0).toUpperCase() + v.slice(1)}
                </button>
              ))}
              <span className="text-xs text-gray-500 ml-2">
                {dashboard.period.start} → {dashboard.period.end}
              </span>
            </div>

            {view === "cumulative" && (
              <>
                <MetricsCards data={cumulativeData} />
                <TrendsChart
                  cumulativeTrend={dashboard.cumulative.trend}
                  channels={[]}
                />
              </>
            )}

            {view === "individual" && (
              <>
                <ChannelCards channels={dashboard.channels} />
                <TrendsChart
                  cumulativeTrend={null}
                  channels={dashboard.channels.filter((c) => !c.error)}
                />
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
