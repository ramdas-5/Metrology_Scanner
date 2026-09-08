import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  CircleUserRound,
  Database,
  FileBarChart,
  FileText,
  Gauge,
  KeyRound,
  Lock,
  RefreshCw,
  Search,
  Server,
  Settings,
  Shield,
  SlidersHorizontal,
  Trash2,
  UserPlus,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { admin as adminApi, getToken, API_URL } from "../lib/api";

const ACTION_ICONS = {
  USER_CREATED: UserPlus,
  USER_ACCESS_MODIFIED: KeyRound,
  SCAN_CREATED: ScanIcon,
  SCAN_CACHE_HIT: Database,
  BACKUP_CREATED: Database,
};

function ScanIcon(props) {
  return <Activity {...props} />;
}

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);

  const [health, setHealth] = useState([]);
  const [loadingHealth, setLoadingHealth] = useState(true);

  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(true);

  const [sysStats, setSysStats] = useState(null);
  const [trend, setTrend] = useState([]);
  const [rules, setRules] = useState([]);

  const [showAddInspector, setShowAddInspector] = useState(false);
  const [newInspector, setNewInspector] = useState({
    name: "",
    email: "",
    password: "",
    role: "inspector",
  });
  const [addingInspector, setAddingInspector] = useState(false);
  const [addInspectorError, setAddInspectorError] = useState("");

  const [showAllInspectors, setShowAllInspectors] = useState(false);
  const [inspectorSearch, setInspectorSearch] = useState("");

  const [busy, setBusy] = useState(""); // tracks which quick-action is running

  const loadAll = () => {
    setLoadingUsers(true);
    adminApi
      .listUsers()
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoadingUsers(false));

    setLoadingHealth(true);
    adminApi
      .systemHealth()
      .then(setHealth)
      .catch(() => setHealth([]))
      .finally(() => setLoadingHealth(false));

    setLoadingLogs(true);
    adminApi
      .auditLogs(20)
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoadingLogs(false));

    adminApi.systemStats().then(setSysStats).catch(() => setSysStats(null));
    adminApi.trend(14).then(setTrend).catch(() => setTrend([]));
    adminApi.rules().then(setRules).catch(() => setRules([]));
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleAddInspector = async (e) => {
    e.preventDefault();
    setAddingInspector(true);
    setAddInspectorError("");
    try {
      await adminApi.createUser(newInspector);
      setShowAddInspector(false);
      setNewInspector({ name: "", email: "", password: "", role: "inspector" });
      loadAll();
    } catch (err) {
      setAddInspectorError(err.message || "Failed to add inspector.");
    } finally {
      setAddingInspector(false);
    }
  };

  const toggleUserActive = async (id) => {
    try {
      await adminApi.toggleUser(id);
      loadAll();
    } catch (err) {
      alert(err.message || "Failed to update user.");
    }
  };

  const deleteUser = async (id, name) => {
    if (!window.confirm(`Delete user "${name}"? This cannot be undone.`)) return;
    try {
      await adminApi.deleteUser(id);
      loadAll();
    } catch (err) {
      alert(err.message || "Failed to delete user.");
    }
  };

  const handleBackup = async () => {
    setBusy("backup");
    try {
      const res = await adminApi.backup();
      // Auto-download the backup file.
      const token = getToken();
      const resp = await fetch(`${API_URL}${res.download_url}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = res.file;
        a.click();
        window.URL.revokeObjectURL(url);
      }
      alert(`Backup created: ${res.file}`);
      loadAll();
    } catch (err) {
      alert(err.message || "Backup failed.");
    } finally {
      setBusy("");
    }
  };

  const handleSystemReport = async () => {
    setBusy("report");
    try {
      await adminApi.summaryReport();
    } catch (err) {
      alert(err.message || "Report generation failed.");
    } finally {
      setBusy("");
    }
  };

  const total = sysStats?.total_inspections ?? 0;
  const passed = sysStats?.passed ?? 0;
  const failed = sysStats?.failed ?? 0;
  const pending = sysStats?.pending ?? 0;
  const passedPct = total ? (passed / total) * 100 : 0;
  const failedPct = total ? (failed / total) * 100 : 0;
  const pendingPct = total ? (pending / total) * 100 : 0;

  const activeInspectorCount = users.filter((u) => u.is_active).length;
  const healthLabel =
    health.length > 0 && health.every((h) => h.status === "Operational")
      ? "Excellent"
      : "Degraded";

  // Trend chart geometry from real data.
  const maxInspections = Math.max(1, ...trend.map((t) => t.inspections));
  const trendPoints = trend.map((t, i) => {
    const x = trend.length > 1 ? (i / (trend.length - 1)) * 600 : 300;
    const y = 170 - (t.inspections / maxInspections) * 150;
    return { x, y, ...t };
  });
  const trendPath = trendPoints
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");
  const trendArea =
    trendPoints.length > 1
      ? `${trendPath} L600 180 L0 180 Z`
      : "";

  // Inspector list (modal) filtered by search.
  const filteredInspectors = users.filter(
    (u) =>
      u.name.toLowerCase().includes(inspectorSearch.toLowerCase()) ||
      u.email.toLowerCase().includes(inspectorSearch.toLowerCase())
  );

  return (
    <main className="min-h-[calc(100vh-70px)] bg-[#f5f8fc] p-4">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-[16px] font-bold text-slate-800">
            Admin Panel Overview
          </h1>
          <p className="mt-0.5 text-[8px] text-slate-400">
            Live data from the backend • Manage users, rules and system operations.
          </p>
        </div>
        <button
          onClick={loadAll}
          className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-[8px] font-semibold text-slate-500 transition hover:bg-slate-50"
          title="Refresh all data"
        >
          <RefreshCw size={11} className={loadingUsers ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* =====================================================
          KPI CARDS
      ===================================================== */}

      <section className="grid grid-cols-2 gap-2.5 lg:grid-cols-6">
        <AdminStat
          title="Total Users"
          value={loadingUsers ? "…" : String(users.length)}
          subtitle="Registered accounts"
          icon={Users}
          iconClass="bg-blue-50 text-blue-600"
        />
        <AdminStat
          title="Active Users"
          value={loadingUsers ? "…" : String(activeInspectorCount)}
          subtitle={
            users.length
              ? `${Math.round((activeInspectorCount / users.length) * 100)}% of total`
              : "--"
          }
          icon={CircleUserRound}
          iconClass="bg-green-50 text-green-600"
        />
        <AdminStat
          title="Total Inspections"
          value={sysStats ? total.toLocaleString() : "…"}
          subtitle="All-time"
          icon={FileText}
          iconClass="bg-blue-50 text-blue-600"
        />
        <AdminStat
          title="Failed Scans"
          value={sysStats ? failed.toLocaleString() : "…"}
          subtitle={`${sysStats?.compliance_rate ?? 0}% pass rate`}
          icon={Shield}
          iconClass="bg-red-50 text-red-600"
        />
        <AdminStat
          title="AI Scans"
          value={sysStats ? sysStats.ai_scans.toLocaleString() : "…"}
          subtitle={`${sysStats?.cache_hits ?? 0} cache hits saved`}
          icon={Activity}
          iconClass="bg-purple-50 text-purple-600"
        />
        <AdminStat
          title="System Health"
          value={loadingHealth ? "…" : healthLabel}
          subtitle={loadingHealth ? "Checking..." : `${health.filter((h) => h.status === "Operational").length}/${health.length} services up`}
          icon={Server}
          iconClass="bg-green-50 text-green-600"
        />
      </section>

      {/* =====================================================
          ROW 1 — TREND / COMPLIANCE / ACTIVITIES
      ===================================================== */}

      <section className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-[1.4fr_0.9fr_1fr]">

        {/* Inspection trend - REAL data */}
        <Panel title="Inspection Trend (Last 14 Days)" icon={BarChart3}>
          <div className="mb-2 flex items-center justify-end gap-3">
            <LegendDot color="bg-blue-500" text="Inspections" />
          </div>

          <div className="relative h-[145px]">
            <div className="absolute inset-0 flex flex-col justify-between">
              {[0, 1, 2, 3, 4].map((item) => (
                <div key={item} className="border-t border-dashed border-slate-100" />
              ))}
            </div>

            {trendPoints.length > 1 ? (
              <svg viewBox="0 0 600 180" preserveAspectRatio="none" className="relative z-10 h-full w-full">
                <path d={trendArea} fill="rgba(37,99,235,0.08)" />
                <path d={trendPath} fill="none" stroke="#2563eb" strokeWidth="2" />
                {trendPoints.map((p) => (
                  <circle key={p.date} cx={p.x} cy={p.y} r="3" fill="#2563eb">
                    <title>{`${p.date}: ${p.inspections} inspections`}</title>
                  </circle>
                ))}
              </svg>
            ) : (
              <div className="flex h-full items-center justify-center text-[8px] text-slate-400">
                No scan data in the last 14 days yet.
              </div>
            )}

            <div className="absolute bottom-0 left-0 right-0 flex justify-between px-1 text-[6px] text-slate-400">
              {trend.length > 0 && (
                <>
                  <span>{trend[0]?.date?.slice(5)}</span>
                  <span>{trend[Math.floor(trend.length / 2)]?.date?.slice(5)}</span>
                  <span>{trend[trend.length - 1]?.date?.slice(5)}</span>
                </>
              )}
            </div>
          </div>
        </Panel>

        {/* Compliance donut - REAL data */}
        <Panel title="Compliance Overview">
          <div className="flex h-[170px] items-center justify-center gap-5">
            <div
              className="relative flex h-[120px] w-[120px] items-center justify-center rounded-full"
              style={{
                background: `conic-gradient(#16a34a 0% ${passedPct}%, #dc2626 ${passedPct}% ${passedPct + failedPct}%, #f59e0b ${passedPct + failedPct}% 100%)`,
              }}
            >
              <div className="flex h-[77px] w-[77px] flex-col items-center justify-center rounded-full bg-white">
                <span className="text-[17px] font-bold text-slate-700">
                  {total.toLocaleString()}
                </span>
                <span className="text-[7px] text-slate-400">Total</span>
              </div>
            </div>

            <div className="space-y-3">
              <ComplianceLegend color="bg-green-500" label="Passed" percentage={`${Math.round(passedPct)}%`} value={passed.toLocaleString()} />
              <ComplianceLegend color="bg-red-500" label="Failed" percentage={`${Math.round(failedPct)}%`} value={failed.toLocaleString()} />
              <ComplianceLegend color="bg-orange-400" label="Pending Review" percentage={`${Math.round(pendingPct)}%`} value={pending.toLocaleString()} />
            </div>
          </div>
        </Panel>

        {/* Activities - REAL audit logs */}
        <Panel
          title="Recent System Activities"
          icon={Activity}
          right={<span className="text-[7px] text-slate-400">Live audit log</span>}
        >
          <div className="space-y-2">
            {loadingLogs && (
              <p className="py-4 text-center text-[7px] text-slate-400">Loading activities...</p>
            )}
            {!loadingLogs && logs.length === 0 && (
              <p className="py-4 text-center text-[7px] text-slate-400">No activity yet.</p>
            )}
            {!loadingLogs &&
              logs.slice(0, 6).map((log) => {
                const Icon = ACTION_ICONS[log.action] || Activity;
                return (
                  <div key={log.id} className="flex gap-2 border-b border-slate-100 pb-2 last:border-0">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-blue-50 text-[#07539a]">
                      <Icon size={11} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex justify-between gap-2">
                        <p className="truncate text-[8px] font-semibold text-slate-600">
                          {log.action.replace(/_/g, " ")}
                        </p>
                        <span className="shrink-0 text-[6px] text-slate-400">
                          {new Date(log.created_at).toLocaleString("en-IN", {
                            day: "2-digit",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <p className="mt-0.5 truncate text-[7px] text-slate-400">
                        {log.user_name || "system"} • {log.details || ""}
                      </p>
                    </div>
                  </div>
                );
              })}
          </div>
        </Panel>
      </section>

      {/* =====================================================
          ROW 2 — MANAGEMENT TABLES
      ===================================================== */}

      <section className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-[1.15fr_1.05fr_1fr]">

        {/* Inspector Management - REAL users with email + scan count */}
        <Panel
          title="User Management (Name • Email • Role)"
          icon={Users}
          right={
            <button
              onClick={() => setShowAllInspectors(true)}
              className="text-[7px] font-semibold text-[#07539a] hover:underline"
            >
              View All →
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[390px]">
              <thead>
                <tr className="border-b border-slate-100">
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Scans</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Action</TableHead>
                </tr>
              </thead>
              <tbody>
                {loadingUsers && (
                  <tr>
                    <td colSpan="6" className="py-4 text-center text-[7px] text-slate-400">
                      Loading users...
                    </td>
                  </tr>
                )}
                {!loadingUsers && users.length === 0 && (
                  <tr>
                    <td colSpan="6" className="py-4 text-center text-[7px] text-slate-400">
                      No users yet. Add one from Quick Actions.
                    </td>
                  </tr>
                )}
                {!loadingUsers &&
                  users.slice(0, 6).map((person) => (
                    <tr key={person.id} className="border-b border-slate-50 last:border-0">
                      <td className="px-1.5 py-2 text-[7px] font-semibold text-slate-600">
                        {person.name}
                      </td>
                      <td className="px-1.5 py-2 text-[7px] text-slate-400">
                        {person.email}
                      </td>
                      <td className="px-1.5 py-2 text-[7px] capitalize text-slate-500">
                        {person.role}
                      </td>
                      <td className="px-1.5 py-2 text-[7px] text-slate-500">
                        {person.scan_count}
                      </td>
                      <td className="px-1.5 py-2">
                        <StatusPill status={person.is_active ? "Active" : "Inactive"} />
                      </td>
                      <td className="px-1.5 py-2">
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => toggleUserActive(person.id)}
                            className="text-[7px] font-semibold text-[#07539a] hover:underline"
                            title={person.is_active ? "Disable user" : "Enable user"}
                          >
                            {person.is_active ? "Disable" : "Enable"}
                          </button>
                          <button
                            onClick={() => deleteUser(person.id, person.name)}
                            className="text-[7px] font-semibold text-red-400 hover:underline"
                            title="Delete user"
                          >
                            <Trash2 size={9} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Panel>

        {/* Rule Management - REAL rules from the compliance engine */}
        <Panel
          title="Rule Management (Active Rules)"
          icon={SlidersHorizontal}
          right={<span className="text-[7px] text-slate-400">{rules.length} rules enforced</span>}
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[380px]">
              <thead>
                <tr className="border-b border-slate-100">
                  <TableHead>Rule Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Rule Ref.</TableHead>
                  <TableHead>Severity</TableHead>
                </tr>
              </thead>
              <tbody>
                {rules.length === 0 && (
                  <tr>
                    <td colSpan="4" className="py-4 text-center text-[7px] text-slate-400">
                      Loading rules...
                    </td>
                  </tr>
                )}
                {rules.map((rule) => (
                  <tr key={rule.code} className="border-b border-slate-50 last:border-0">
                    <td className="px-1.5 py-2 text-[7px] font-semibold text-slate-600">
                      {rule.name}
                    </td>
                    <td className="px-1.5 py-2 text-[7px] text-slate-500">
                      {rule.category}
                    </td>
                    <td className="px-1.5 py-2 text-[7px] text-slate-500">
                      {rule.rule_reference}
                    </td>
                    <td className="px-1.5 py-2">
                      <span
                        className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-[6px] font-semibold ${
                          rule.severity === "major"
                            ? "bg-red-50 text-red-500"
                            : "bg-amber-50 text-amber-600"
                        }`}
                      >
                        {rule.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        {/* Violation categories - REAL top violations */}
        <Panel
          title="Top Violations (All Time)"
          icon={AlertTriangle}
        >
          <div className="space-y-2">
            {loadingUsers && (
              <p className="py-4 text-center text-[7px] text-slate-400">Loading...</p>
            )}
            {!loadingUsers && (sysStats?.top_violations ?? []).length === 0 && (
              <p className="py-4 text-center text-[7px] text-slate-400">
                No violations recorded yet — all scanned labels are compliant so far.
              </p>
            )}
            {(sysStats?.top_violations ?? []).map((item) => (
              <div key={item.label}>
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-[7px] font-medium text-slate-600">{item.label}</span>
                  <div className="flex gap-2">
                    <span className="text-[7px] font-semibold text-slate-600">{item.value}</span>
                    <span className="text-[7px] text-slate-400">{item.percentage}</span>
                  </div>
                </div>
                <div className="h-[4px] rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-red-400"
                    style={{ width: `${Math.max(12, parseFloat(item.percentage) || 0)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-[7px]">
            <div className="rounded-md bg-slate-50 px-2 py-1.5">
              <p className="text-slate-400">Avg confidence</p>
              <p className="font-bold text-slate-600">{sysStats?.avg_overall_confidence ?? 0}%</p>
            </div>
            <div className="rounded-md bg-slate-50 px-2 py-1.5">
              <p className="text-slate-400">Avg score</p>
              <p className="font-bold text-slate-600">{sysStats?.avg_compliance_score ?? 0}%</p>
            </div>
          </div>
        </Panel>
      </section>

      {/* =====================================================
          ROW 3
      ===================================================== */}

      <section className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-[1fr_1fr_1fr_1fr]">

        {/* System Health - REAL */}
        <Panel title="System Health" icon={Gauge}>
          <div className="space-y-2">
            {loadingHealth && (
              <p className="py-3 text-center text-[7px] text-slate-400">Checking services...</p>
            )}
            {systemHealthRows(health).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="flex h-5 w-5 items-center justify-center rounded bg-slate-50 text-slate-500">
                    <Server size={10} />
                  </div>
                  <span className="text-[7px] font-medium text-slate-600">{name}</span>
                </div>
                <span
                  className={`flex items-center gap-1 text-[6.5px] font-semibold ${
                    status === "Operational" ? "text-green-600" : "text-amber-500"
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      status === "Operational" ? "bg-green-500" : "bg-amber-400"
                    }`}
                  />
                  {status}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        {/* AI pipeline - REAL numbers */}
        <Panel title="AI Pipeline" icon={Activity}>
          <div className="flex items-center gap-4">
            <div
              className="relative flex h-20 w-20 shrink-0 items-center justify-center rounded-full"
              style={{
                background: `conic-gradient(#16a34a 0% ${sysStats?.compliance_rate ?? 0}%, #e2e8f0 ${sysStats?.compliance_rate ?? 0}% 100%)`,
              }}
            >
              <div className="flex h-[57px] w-[57px] flex-col items-center justify-center rounded-full bg-white">
                <span className="text-[13px] font-bold text-slate-700">
                  {sysStats?.compliance_rate ?? 0}%
                </span>
                <span className="text-[6px] text-slate-400">Pass rate</span>
              </div>
            </div>

            <div className="flex-1 space-y-2">
              <Performance label="AI-extracted scans" value={sysStats ? `${sysStats.ai_scans}` : "…"} />
              <Performance label="Cache hits (no AI call)" value={sysStats ? `${sysStats.cache_hits}` : "…"} />
              <Performance label="Avg compliance score" value={sysStats ? `${sysStats.avg_compliance_score}%` : "…"} />
              <Performance label="Avg OCR confidence" value={sysStats ? `${sysStats.avg_overall_confidence}%` : "…"} />
            </div>
          </div>
        </Panel>

        {/* Audit logs - REAL with user names */}
        <Panel
          title="Audit Logs (Latest)"
          icon={FileText}
          right={<span className="text-[7px] text-slate-400">last 20</span>}
        >
          <div className="max-h-[150px] space-y-2 overflow-y-auto">
            {loadingLogs && (
              <p className="py-3 text-center text-[7px] text-slate-400">Loading logs...</p>
            )}
            {!loadingLogs && logs.length === 0 && (
              <p className="py-3 text-center text-[7px] text-slate-400">No logs yet.</p>
            )}
            {!loadingLogs &&
              logs.map((log) => (
                <div key={log.id} className="border-b border-slate-100 pb-2 last:border-0">
                  <div className="flex justify-between gap-2">
                    <span className="text-[7px] font-semibold text-slate-600">
                      {log.action.replace(/_/g, " ")}
                    </span>
                    <span className="shrink-0 text-[6px] text-slate-400">
                      {new Date(log.created_at).toLocaleString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[6px] text-slate-400">
                    User: {log.user_name || "system"} • {log.details || ""}
                  </p>
                </div>
              ))}
          </div>
        </Panel>

        {/* Quick Actions - ALL WIRED */}
        <Panel title="Quick Actions" icon={Settings}>
          <div className="grid grid-cols-2 gap-2">
            <QuickAction
              icon={UserPlus}
              text="Add New User"
              onClick={() => setShowAddInspector(true)}
            />
            <QuickAction
              icon={Users}
              text="All Inspectors"
              onClick={() => setShowAllInspectors(true)}
            />
            <QuickAction
              icon={FileBarChart}
              text={busy === "report" ? "Generating..." : "System Report PDF"}
              onClick={handleSystemReport}
              disabled={busy === "report"}
            />
            <QuickAction
              icon={Lock}
              text={busy === "backup" ? "Backing up..." : "Backup Now"}
              onClick={handleBackup}
              disabled={busy === "backup"}
            />
            <QuickAction icon={RefreshCw} text="Refresh Data" onClick={loadAll} />
            <QuickAction
              icon={CheckCircle2}
              text="Check Health"
              onClick={() => {
                adminApi
                  .systemHealth()
                  .then(setHealth)
                  .then(() => alert("System health refreshed."))
                  .catch(() => alert("Health check failed."));
              }}
            />
          </div>
        </Panel>
      </section>

      {/* =====================================================
          FOOTER
      ===================================================== */}

      <div className="mt-3 flex items-center justify-between px-1">
        <p className="text-[7px] text-slate-400">
          Metrology Scanner • Administration Console
        </p>
        <p className="text-[7px] text-slate-400">
          System status:{" "}
          <span className={`font-semibold ${healthLabel === "Excellent" ? "text-green-600" : "text-amber-500"}`}>
            {loadingHealth ? "Checking..." : healthLabel}
          </span>
        </p>
      </div>

      {/* =====================================================
          ADD USER MODAL
      ===================================================== */}

      {showAddInspector && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
          onClick={() => setShowAddInspector(false)}
        >
          <form
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleAddInspector}
            className="w-full max-w-sm rounded-xl bg-white p-5 shadow-2xl"
          >
            <h2 className="text-[13px] font-bold text-slate-800">Add New User</h2>
            <p className="mt-1 text-[8px] text-slate-400">
              Creates a real login account on the backend.
            </p>

            <div className="mt-4 space-y-2.5">
              <div>
                <label className="mb-1 block text-[7px] font-semibold text-slate-500">Full Name</label>
                <input
                  required
                  value={newInspector.name}
                  onChange={(e) => setNewInspector((s) => ({ ...s, name: e.target.value }))}
                  className="h-8 w-full rounded-md border border-slate-300 px-2.5 text-[9px] outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-[7px] font-semibold text-slate-500">Email</label>
                <input
                  type="email"
                  required
                  value={newInspector.email}
                  onChange={(e) => setNewInspector((s) => ({ ...s, email: e.target.value }))}
                  className="h-8 w-full rounded-md border border-slate-300 px-2.5 text-[9px] outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-[7px] font-semibold text-slate-500">
                  Temporary Password
                </label>
                <input
                  type="password"
                  required
                  value={newInspector.password}
                  onChange={(e) => setNewInspector((s) => ({ ...s, password: e.target.value }))}
                  className="h-8 w-full rounded-md border border-slate-300 px-2.5 text-[9px] outline-none focus:border-blue-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-[7px] font-semibold text-slate-500">Role</label>
                <select
                  value={newInspector.role}
                  onChange={(e) => setNewInspector((s) => ({ ...s, role: e.target.value }))}
                  className="h-8 w-full rounded-md border border-slate-300 px-2.5 text-[9px] outline-none focus:border-blue-400"
                >
                  <option value="inspector">Inspector</option>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
            </div>

            {addInspectorError && (
              <p className="mt-3 rounded-md bg-red-50 px-2.5 py-2 text-[8px] font-medium text-red-600">
                {addInspectorError}
              </p>
            )}

            <div className="mt-4 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setShowAddInspector(false)}
                className="h-9 rounded-md border border-slate-300 text-[9px] font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={addingInspector}
                className="h-9 rounded-md bg-[#07539a] text-[9px] font-semibold text-white hover:bg-[#06447f] disabled:opacity-50"
              >
                {addingInspector ? "Adding..." : "Add User"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* =====================================================
          ALL INSPECTORS MODAL (searchable, with email)
      ===================================================== */}

      {showAllInspectors && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
          onClick={() => setShowAllInspectors(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-xl bg-white p-5 shadow-2xl"
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-[13px] font-bold text-slate-800">
                  All Inspectors & Users
                </h2>
                <p className="mt-1 text-[8px] text-slate-400">
                  {users.length} account{users.length === 1 ? "" : "s"} • name, email and activity
                </p>
              </div>
              <button
                onClick={() => setShowAllInspectors(false)}
                className="rounded p-1 text-slate-400 hover:bg-slate-100"
              >
                <X size={14} />
              </button>
            </div>

            <div className="relative mt-3">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                value={inspectorSearch}
                onChange={(e) => setInspectorSearch(e.target.value)}
                placeholder="Search by name or email..."
                className="h-8 w-full rounded-md border border-slate-300 pl-8 pr-3 text-[9px] outline-none focus:border-blue-400"
              />
            </div>

            <div className="mt-3 max-h-[320px] overflow-y-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <TableHead>Inspector Name</TableHead>
                    <TableHead>Email ID</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Scans</TableHead>
                    <TableHead>Status</TableHead>
                  </tr>
                </thead>
                <tbody>
                  {filteredInspectors.length === 0 && (
                    <tr>
                      <td colSpan="5" className="py-4 text-center text-[8px] text-slate-400">
                        No users match your search.
                      </td>
                    </tr>
                  )}
                  {filteredInspectors.map((u) => (
                    <tr key={u.id} className="border-b border-slate-50">
                      <td className="py-2 pr-2 text-[8px] font-semibold text-slate-700">
                        <span className="flex items-center gap-1.5">
                          <UserRound size={10} className="text-slate-400" />
                          {u.name}
                        </span>
                      </td>
                      <td className="py-2 pr-2 text-[8px] text-slate-500">{u.email}</td>
                      <td className="py-2 pr-2 text-[8px] capitalize text-slate-500">{u.role}</td>
                      <td className="py-2 pr-2 text-[8px] text-slate-500">{u.scan_count}</td>
                      <td className="py-2">
                        <StatusPill status={u.is_active ? "Active" : "Inactive"} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              onClick={() => setShowAllInspectors(false)}
              className="mt-4 h-9 w-full rounded-md border border-slate-300 text-[9px] font-semibold text-slate-600 hover:bg-slate-50"
            >
              CLOSE
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

/* Small helper so the health rows degrade gracefully while loading */
function systemHealthRows(health) {
  return health.map((h) => [h.component, h.status]);
}

/* ============================================================
   ADMIN STAT
============================================================ */

function AdminStat({ title, value, subtitle, icon: Icon, iconClass }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[6.5px] font-medium text-slate-400">{title}</p>
          <p className="mt-1 text-[15px] font-bold text-slate-700">{value}</p>
          <p className="mt-0.5 text-[6px] text-green-500">{subtitle}</p>
        </div>
        <div className={`flex h-7 w-7 items-center justify-center rounded-md ${iconClass}`}>
          <Icon size={13} />
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   PANEL
============================================================ */

function Panel({ title, icon: Icon, children, right }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {Icon && <Icon size={12} className="text-[#07539a]" />}
          <h2 className="text-[9px] font-bold text-slate-700">{title}</h2>
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

/* ============================================================
   TABLE HEAD
============================================================ */

function TableHead({ children }) {
  return (
    <th className="px-1.5 py-1.5 text-left text-[6px] font-semibold uppercase tracking-wide text-slate-400">
      {children}
    </th>
  );
}

/* ============================================================
   STATUS PILL
============================================================ */

function StatusPill({ status }) {
  const active = status === "Active";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[6px] font-semibold ${
        active ? "bg-green-50 text-green-600" : "bg-red-50 text-red-500"
      }`}
    >
      <span className={`h-1 w-1 rounded-full ${active ? "bg-green-500" : "bg-red-500"}`} />
      {status}
    </span>
  );
}

/* ============================================================
   LEGEND DOT
============================================================ */

function LegendDot({ color, text }) {
  return (
    <span className="flex items-center gap-1 text-[6px] text-slate-400">
      <span className={`h-1.5 w-1.5 rounded-full ${color}`} />
      {text}
    </span>
  );
}

/* ============================================================
   COMPLIANCE LEGEND
============================================================ */

function ComplianceLegend({ color, label, percentage, value }) {
  return (
    <div className="flex items-start gap-1.5">
      <span className={`mt-0.5 h-2 w-2 rounded-sm ${color}`} />
      <div>
        <div className="flex items-center gap-1.5">
          <span className="text-[7px] font-medium text-slate-600">{label}</span>
          <span className="text-[7px] font-bold text-slate-700">{value}</span>
        </div>
        <span className="text-[6px] text-slate-400">{percentage}</span>
      </div>
    </div>
  );
}

/* ============================================================
   PERFORMANCE
============================================================ */

function Performance({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[6.5px] text-slate-500">{label}</span>
      <span className="text-[7px] font-semibold text-green-600">{value}</span>
    </div>
  );
}

/* ============================================================
   QUICK ACTION
============================================================ */

function QuickAction({ icon: Icon, text, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex min-h-[40px] items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2 text-left transition hover:border-blue-200 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-blue-50 text-[#07539a]">
        <Icon size={11} />
      </div>
      <span className="text-[6.5px] font-semibold leading-3 text-slate-600">{text}</span>
    </button>
  );
}
