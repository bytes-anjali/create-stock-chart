import React from "react";

function fmt(n) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function Bar({ pct, color }) {
  return (
    <div className="w-full bg-yt-border rounded-full h-1 overflow-hidden">
      <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function ChannelCards({ channels }) {
  if (!channels?.length) return null;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
      {channels.map((ch) => {
        if (ch.error) {
          return (
            <div key={ch.id} className="card opacity-50">
              <p className="text-sm font-medium text-white truncate">{ch.id}</p>
              <p className="text-xs text-red-400 mt-1">{ch.error}</p>
            </div>
          );
        }
        const a = ch.analytics || {};
        const v = ch.videos || {};
        const lfViewPct = a.views ? Math.round((a.lf_views / a.views) * 100) : 0;
        const lfVideoPct = v.total ? Math.round((v.lf / v.total) * 100) : 0;

        return (
          <div key={ch.id} className="card space-y-3">
            <div className="flex items-center gap-2 min-w-0">
              {ch.thumbnail && (
                <img src={ch.thumbnail} alt="" className="w-8 h-8 rounded-full flex-shrink-0" />
              )}
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">{ch.title}</p>
                <p className="text-xs text-gray-500 truncate">{ch.accountId}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <div>
                <p className="text-gray-400">Views</p>
                <p className="text-white font-semibold">{fmt(a.views)}</p>
                <Bar pct={lfViewPct} color="bg-blue-500" />
                <p className="text-gray-500 mt-0.5">LF {fmt(a.lf_views)} · SF {fmt(a.sf_views)}</p>
              </div>
              <div>
                <p className="text-gray-400">Videos</p>
                <p className="text-white font-semibold">{fmt(v.total)}</p>
                <Bar pct={lfVideoPct} color="bg-blue-500" />
                <p className="text-gray-500 mt-0.5">LF {v.lf} · SF {v.sf}</p>
              </div>
              <div>
                <p className="text-gray-400">Impressions</p>
                <p className="text-white font-semibold">{fmt(a.impressions)}</p>
              </div>
              <div>
                <p className="text-gray-400">CTR</p>
                <p className="text-white font-semibold">{a.ctr != null ? `${a.ctr}%` : "—"}</p>
              </div>
              <div>
                <p className="text-gray-400">AVP</p>
                <p className="text-white font-semibold">{a.avgViewPercentage != null ? `${a.avgViewPercentage}%` : "—"}</p>
              </div>
              <div>
                <p className="text-gray-400">Subs</p>
                <p className="text-green-400 font-semibold">+{fmt(a.subscribersGained)}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
