const BASE = "/api";

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  getAccounts: () => req("/accounts"),
  deleteAccount: (id) => req(`/accounts/${id}`, { method: "DELETE" }),
  getAuthUrl: (accountId) => req(`/auth/url?account_id=${encodeURIComponent(accountId)}`),
  getChannels: () => req("/channels"),
  getDashboard: (channelIds, startDate, endDate) => {
    const ids = channelIds.join(",");
    return req(
      `/dashboard?channel_ids=${encodeURIComponent(ids)}&start_date=${startDate}&end_date=${endDate}`
    );
  },
};
