import React, { useState, useRef, useEffect } from "react";

export default function ChannelSelector({ channels, selected, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handle(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  const toggle = (id) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const allSelected = channels.length > 0 && selected.length === channels.length;
  const toggleAll = () => onChange(allSelected ? [] : channels.map((c) => c.id));

  const label =
    selected.length === 0
      ? "Select channels…"
      : selected.length === channels.length
      ? "All channels"
      : `${selected.length} channel${selected.length > 1 ? "s" : ""}`;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 bg-yt-card border border-yt-border rounded-lg px-3 py-2 text-sm hover:border-gray-500 transition-colors min-w-[180px]"
      >
        <span className="flex-1 text-left truncate">{label}</span>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute top-full mt-1 left-0 z-50 bg-yt-card border border-yt-border rounded-xl shadow-2xl py-2 min-w-[260px] max-h-72 overflow-y-auto">
          {channels.length === 0 && (
            <p className="text-xs text-gray-500 px-4 py-2">No channels found. Add an account first.</p>
          )}
          {channels.length > 0 && (
            <label className="flex items-center gap-3 px-4 py-2 hover:bg-yt-border cursor-pointer">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={toggleAll}
                className="accent-yt-red"
              />
              <span className="text-sm font-medium text-white">All Channels</span>
            </label>
          )}
          {channels.length > 0 && <hr className="border-yt-border my-1" />}
          {channels.map((ch) => (
            <label key={ch.id} className="flex items-center gap-3 px-4 py-2 hover:bg-yt-border cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(ch.id)}
                onChange={() => toggle(ch.id)}
                className="accent-yt-red"
              />
              {ch.thumbnail && (
                <img src={ch.thumbnail} alt="" className="w-6 h-6 rounded-full flex-shrink-0" />
              )}
              <div className="min-w-0">
                <p className="text-sm text-white truncate">{ch.title}</p>
                <p className="text-xs text-gray-500 truncate">{ch.accountId}</p>
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
