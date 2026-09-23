import { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bell,
  Database,
  KeyRound,
  RefreshCw,
  ScanLine,
  UserPlus,
  X,
} from "lucide-react";
import { dashboard as dashboardApi } from "../lib/api";

const ACTION_ICONS = {
  SCAN_CREATED: ScanLine,
  SCAN_CACHE_HIT: Database,
  USER_CREATED: UserPlus,
  USER_ACCESS_MODIFIED: KeyRound,
  BACKUP_CREATED: Database,
};

const LAST_SEEN_KEY = "metrology_notifications_last_seen";

function actionLabel(action) {
  switch (action) {
    case "SCAN_CREATED":
      return "New scan completed";
    case "SCAN_CACHE_HIT":
      return "Scan served from cache";
    case "USER_CREATED":
      return "New user account";
    case "USER_ACCESS_MODIFIED":
      return "User access changed";
    case "BACKUP_CREATED":
      return "Database backup";
    default:
      return (action || "Activity").replace(/_/g, " ");
  }
}

function timeAgo(iso) {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Math.max(0, Date.now() - then);
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
  });
}

function readLastSeen() {
  try {
    return parseInt(localStorage.getItem(LAST_SEEN_KEY) || "0", 10) || 0;
  } catch {
    return 0;
  }
}

function writeLastSeen(ts) {
  try {
    localStorage.setItem(LAST_SEEN_KEY, String(ts));
  } catch {
    // storage unavailable - badge just resets every reload
  }
}

export default function Notifications() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastSeen, setLastSeen] = useState(readLastSeen);
  const boxRef = useRef(null);

  // One fetch path used by mount, polling, refresh and open - so state can
  // never get out of sync between them.
  const fetchActivity = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await dashboardApi.recentActivity(10);
      setItems(Array.isArray(data) ? data : []);
      setError("");
    } catch (err) {
      // Surface the error instead of failing silently - the panel shows a
      // retry button, so a dead backend is visible rather than "empty".
      setError(err?.message || "Could not load notifications.");
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  // Initial fetch (badge accuracy) + periodic refresh every 60s.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- feed load on mount is intentional
    fetchActivity();
    const t = setInterval(() => fetchActivity(true), 60000);
    return () => clearInterval(t);
  }, [fetchActivity]);

  // Refresh when the panel opens so the list is never stale.
  useEffect(() => {
    if (open)
      // eslint-disable-next-line react-hooks/set-state-in-effect -- silent refetch on open
      fetchActivity(true);
  }, [open, fetchActivity]);

  // Close on outside pointer press / Escape.
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown, true);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown, true);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const unread = items.filter((n) => {
    const t = new Date(n.created_at).getTime();
    return Number.isFinite(t) && t > lastSeen;
  }).length;

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) {
      // Opening the panel marks everything as read.
      const now = Date.now();
      writeLastSeen(now);
      setLastSeen(now);
    }
  };

  return (
    <div className="relative z-[120]" ref={boxRef}>
      <button
        type="button"
        onClick={toggle}
        title="Notifications"
        aria-label="Notifications"
        aria-expanded={open}
        className="relative flex h-8 w-8 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-[#07539a]"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full border border-white bg-red-500 px-1 text-[7px] font-bold leading-none text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 top-[calc(100%+10px)] w-[340px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl"
          role="dialog"
          aria-label="Notifications panel"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-4 py-3">
            <div>
              <p className="text-[10px] font-bold text-slate-700">Notifications</p>
              <p className="text-[7px] text-slate-400">Latest system activity</p>
            </div>
            <button
              type="button"
              onClick={() => fetchActivity()}
              title="Refresh"
              className="flex h-6 w-6 items-center justify-center rounded text-slate-400 transition hover:bg-slate-200 hover:text-[#07539a]"
            >
              <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            </button>
          </div>

          {/* Body */}
          <div className="max-h-[360px] overflow-y-auto">
            {loading && items.length === 0 && (
              <p className="py-8 text-center text-[8px] text-slate-400">
                Loading notifications...
              </p>
            )}

            {!loading && error && (
              <div className="px-4 py-6 text-center">
                <AlertTriangle size={16} className="mx-auto text-amber-400" />
                <p className="mt-2 text-[8px] font-medium text-red-500">{error}</p>
                <button
                  type="button"
                  onClick={() => fetchActivity()}
                  className="mt-2 rounded-md border border-slate-200 px-3 py-1.5 text-[8px] font-semibold text-[#07539a] transition hover:bg-blue-50"
                >
                  Try again
                </button>
              </div>
            )}

            {!loading && !error && items.length === 0 && (
              <div className="py-8 text-center">
                <Bell size={20} className="mx-auto text-slate-200" />
                <p className="mt-2 text-[8px] text-slate-400">No notifications yet.</p>
              </div>
            )}

            {!loading &&
              !error &&
              items.map((n) => {
                const Icon = ACTION_ICONS[n.action] || Activity;
                const t = new Date(n.created_at).getTime();
                const isUnread = Number.isFinite(t) && t > lastSeen;
                return (
                  <div
                    key={n.id}
                    className={`flex gap-2.5 border-b border-slate-50 px-4 py-2.5 transition last:border-0 ${
                      isUnread ? "bg-blue-50/50" : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-[#07539a]">
                      <Icon size={13} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-[9px] font-semibold text-slate-700">
                          {actionLabel(n.action)}
                        </p>
                        <span className="shrink-0 text-[7px] text-slate-400">
                          {timeAgo(n.created_at)}
                        </span>
                      </div>
                      <p className="mt-0.5 line-clamp-2 text-[8px] leading-4 text-slate-500">
                        {n.details || "System activity"}
                      </p>
                      {n.user_name && (
                        <p className="mt-0.5 text-[7px] text-slate-400">
                          by {n.user_name}
                        </p>
                      )}
                    </div>
                    {isUnread && (
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                    )}
                  </div>
                );
              })}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/70 px-4 py-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="flex items-center gap-1 text-[8px] font-semibold text-slate-500 transition hover:text-[#07539a]"
            >
              <X size={10} />
              Close
            </button>
            <p className="text-[7px] text-slate-400">
              {items.length} recent event{items.length === 1 ? "" : "s"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
