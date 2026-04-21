import React from "react";

function fmt(n, opts = {}) {
  if (n == null) return "—";
  if (opts.pct) return `${Number(n).toFixed(1)}%`;
  if (opts.time) {
    const m = Math.floor(n / 60);
    const s = n % 60;
    return `${m}m ${s}s`;
  }
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function Card({ label, value, sub, accent }) {
  return (
    <div className="card flex flex-col gap-1 min-w-0">
      <span className="metric-label">{label}</span>
      <span className={`metric-value ${accent ? "text-" + accent + "-400" : ""}`}>{value}</span>
      {sub && <span className="metric-sub">{sub}</span>}
    </div>
  );
}

function SplitCard({ label, lf, sf, total }) {
  const lfPct = total ? Math.round((lf / total) * 100) : 0;
  const sfPct = 100 - lfPct;
  return (
    <div className="card flex flex-col gap-2 min-w-0">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{fmt(total)}</span>
      <div className="flex gap-1 mt-1">
        <div className="flex-1 bg-yt-border rounded-full h-1.5 overflow-hidden">
          <div className="bg-blue-500 h-full" style={{ width: `${lfPct}%` }} />
        </div>
      </div>
      <div className="flex justify-between text-xs text-gray-400">
        <span className="text-blue-400">LF {fmt(lf)} ({lfPct}%)</span>
        <span className="text-pink-400">SF {fmt(sf)} ({sfPct}%)</span>
      </div>
    </div>
  );
}

export default function MetricsCards({ data }) {
  if (!data) return null;
  const { views, lf_views, sf_views, impressions, ctr, avgViewPercentage, avgViewDuration, subscribers, subscribersGained, subscribersLost, videos } = data;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      <SplitCard
        label="Views"
        total={views}
        lf={lf_views}
        sf={sf_views}
      />
      <SplitCard
        label="Content Library"
        total={videos?.total}
        lf={videos?.lf}
        sf={videos?.sf}
      />
      <Card
        label="Impressions"
        value={fmt(impressions)}
      />
      <Card
        label="CTR"
        value={fmt(ctr, { pct: true })}
        sub="Click-through rate"
      />
      <Card
        label="Avg View %"
        value={fmt(avgViewPercentage, { pct: true })}
        sub="Avg view percentage (AVP)"
      />
      <Card
        label="Avg View Duration"
        value={fmt(avgViewDuration, { time: true })}
      />
      <Card
        label="Subscribers"
        value={fmt(subscribers ?? data.netSubscribers)}
        sub={
          subscribersGained != null
            ? `+${fmt(subscribersGained)} / -${fmt(subscribersLost)}`
            : undefined
        }
        accent="green"
      />
    </div>
  );
}
