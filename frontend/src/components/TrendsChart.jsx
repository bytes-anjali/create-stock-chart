import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";

const COLORS = [
  "#FF0000", "#3B82F6", "#10B981", "#F59E0B",
  "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16",
];

function fmtNum(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-yt-card border border-yt-border rounded-lg p-3 text-sm shadow-xl">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <span className="font-bold text-white">{fmtNum(p.value)}</span>
        </p>
      ))}
    </div>
  );
}

export default function TrendsChart({ cumulativeTrend, channels }) {
  const [metric, setMetric] = useState("views");

  // Build combined trend: cumulative + per-channel
  const cumulativeData = (cumulativeTrend || []).map((d) => ({
    date: format(parseISO(d.date), "MMM d"),
    cumulative: d[metric] ?? 0,
  }));

  // Merge per-channel trends into one array keyed by date
  const channelMap = {};
  (channels || []).forEach((ch, idx) => {
    if (!ch.analytics?.trend) return;
    ch.analytics.trend.forEach((d) => {
      const dateKey = format(parseISO(d.date), "MMM d");
      if (!channelMap[dateKey]) channelMap[dateKey] = { date: dateKey };
      channelMap[dateKey][ch.id] = d[metric] ?? 0;
    });
  });

  const showIndividual = (channels || []).length > 1;
  const chartData = showIndividual
    ? Object.values(channelMap).sort((a, b) => (a.date > b.date ? 1 : -1))
    : cumulativeData;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white">Trends</h3>
        <div className="flex gap-2">
          {["views", "impressions"].map((m) => (
            <button
              key={m}
              onClick={() => setMetric(m)}
              className={`text-xs px-3 py-1 rounded-full transition-colors ${
                metric === m
                  ? "bg-yt-red text-white"
                  : "bg-yt-border text-gray-400 hover:text-white"
              }`}
            >
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#3F3F3F" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={fmtNum}
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 12, color: "#9CA3AF" }}
          />
          {showIndividual
            ? (channels || []).map((ch, idx) => (
                <Line
                  key={ch.id}
                  type="monotone"
                  dataKey={ch.id}
                  name={ch.title || ch.id}
                  stroke={COLORS[idx % COLORS.length]}
                  dot={false}
                  strokeWidth={2}
                />
              ))
            : (
              <Line
                type="monotone"
                dataKey="cumulative"
                name="All Channels"
                stroke="#FF0000"
                dot={false}
                strokeWidth={2}
              />
            )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
