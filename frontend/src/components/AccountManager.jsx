import React, { useState } from "react";
import { api } from "../api.js";

export default function AccountManager({ accounts, onRefresh }) {
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function addAccount(e) {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setLoading(true);
    setError(null);
    try {
      const { url } = await api.getAuthUrl(name);
      window.open(url, "_self");
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  async function removeAccount(id) {
    if (!confirm(`Remove account "${id}"? This will revoke its token.`)) return;
    try {
      await api.deleteAccount(id);
      onRefresh();
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <div className="card space-y-4">
      <h3 className="font-semibold text-white">Google Accounts</h3>

      {accounts.length === 0 && (
        <p className="text-sm text-gray-400">No accounts connected yet.</p>
      )}

      <div className="space-y-2">
        {accounts.map((acc) => (
          <div
            key={acc.id}
            className="flex items-center justify-between gap-2 text-sm bg-yt-dark rounded-lg px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${acc.valid ? "bg-green-500" : "bg-red-500"}`} />
              <span className="text-white truncate">{acc.id}</span>
              {!acc.valid && <span className="text-xs text-red-400">(token expired)</span>}
            </div>
            <button
              onClick={() => removeAccount(acc.id)}
              className="text-gray-500 hover:text-red-400 transition-colors text-xs flex-shrink-0"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <form onSubmit={addAccount} className="flex gap-2">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Account label (e.g. personal, brand)"
          className="flex-1 bg-yt-dark border border-yt-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-400"
        />
        <button
          type="submit"
          disabled={loading || !newName.trim()}
          className="btn-primary text-sm disabled:opacity-50"
        >
          {loading ? "…" : "Connect"}
        </button>
      </form>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <p className="text-xs text-gray-500">
        Each unique Google account needs one connection. Channels are auto-discovered after auth.
      </p>
    </div>
  );
}
