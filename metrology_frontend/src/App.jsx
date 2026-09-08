import { useEffect, useState } from "react";

import {
  Bell,
  Camera,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Database,
  FileText,
  History,
  LayoutDashboard,
  LogOut,
  ScanLine,
  Settings,
  ShieldCheck,
  TrendingUp,
  UserRound,
  Users,
  XCircle,
} from "lucide-react";

import NewScan from "./components/NewScan";
import ScanHistory from "./components/ScanHistory";
import Reports from "./components/Reports";
import AdminPanel from "./components/AdminPanel";
import Login from "./components/Login";
import { useAuth } from "./context/AuthContext";
import { dashboard as dashboardApi } from "./lib/api";

/* =========================================================
   DASHBOARD PAGE
========================================================= */

function Dashboard({ onNewScan }) {

  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    let cancelled = false;

    dashboardApi
      .stats("Daily")
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch(() => {
        if (!cancelled) setStats(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingStats(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const totalScans = loadingStats ? "…" : stats?.total_inspections ?? 0;
  const violations = loadingStats ? "…" : stats?.violations ?? 0;
  const compliant = loadingStats ? "…" : stats?.compliant ?? 0;
  const complianceRate = loadingStats ? "…" : `${stats?.compliance_rate ?? 0}%`;

  return (
    <main className="space-y-4 p-5">

      {/* =====================================================
          INSPECTION WORKFLOW
      ===================================================== */}

     


      {/* =====================================================
          STATISTICS
      ===================================================== */}

      <section className="grid grid-cols-1 gap-3 md:grid-cols-3">

        <StatCard
          title="Total Scans Today"
          value={totalScans}
          change="Live from backend"
          icon={FileText}
          iconClass="bg-blue-50 text-blue-600"
          changeClass="text-slate-400"
        />

        <StatCard
          title="Violations Detected"
          value={violations}
          change="Live from backend"
          icon={XCircle}
          iconClass="bg-red-50 text-red-500"
          changeClass="text-slate-400"
        />

        <StatCard
          title="Passed Inspections"
          value={compliant}
          change="Live from backend"
          icon={CheckCircle2}
          iconClass="bg-green-50 text-green-500"
          changeClass="text-slate-400"
        />

      </section>


      {/* =====================================================
          NEW PRODUCT SCAN
      ===================================================== */}

      <button
        onClick={onNewScan}
        className="group flex h-[120px] w-full flex-col items-center justify-center rounded-lg bg-gradient-to-r from-[#06366c] to-[#07539a] text-white shadow-md transition hover:scale-[1.005] hover:shadow-lg"
      >

        <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-md border border-white/60 transition group-hover:scale-110">

          <Camera size={22} />

        </div>

        <h2 className="text-[17px] font-bold tracking-wide">
          SCAN NEW PRODUCT
        </h2>

        <p className="mt-1 text-[9px] text-blue-100">
          Click to start a new inspection
        </p>

      </button>


      {/* =====================================================
          LOWER METRICS
      ===================================================== */}

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">

        <MetricCard
          title="Pending Review"
          value={
            loadingStats
              ? "…"
              : String(
                  Math.max(
                    0,
                    (stats?.total_inspections ?? 0) -
                      (stats?.compliant ?? 0) -
                      (stats?.violations ?? 0)
                  )
                )
          }
          icon={Clock3}
          iconClass="bg-orange-50 text-orange-500"
        />

        <MetricCard
          title="Today's Reports"
          value={totalScans}
          icon={FileText}
          iconClass="bg-blue-50 text-blue-600"
        />

        <MetricCard
          title="Compliance Rate"
          value={complianceRate}
          icon={TrendingUp}
          iconClass="bg-green-50 text-green-500"
        />

        <MetricCard
          title="Top Violation"
          value={
            loadingStats
              ? "…"
              : stats?.top_violations?.[0]?.label ?? "None"
          }
          icon={Settings}
          iconClass="bg-purple-50 text-purple-500"
        />

      </section>


      {/* =====================================================
          SYSTEM FOOTER
      ===================================================== */}

      <div className="flex flex-col justify-between gap-1 px-1 pt-1 sm:flex-row">

        <p className="text-[8px] text-slate-400">
          Metrology Scanner • Legal Metrology Compliance Platform
        </p>

        <p className="text-[8px] text-slate-400">
          AI Engine v2.4 • System Operational
        </p>

      </div>

    </main>
  );
}


/* =========================================================
   STAT CARD
========================================================= */

function StatCard({
  title,
  value,
  change,
  icon: Icon,
  iconClass,
  changeClass,
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-sm">

      <div>

        <p className="text-[9px] font-medium text-slate-500">
          {title}
        </p>

        <div className="mt-1 flex items-end gap-2">

          <h3 className="text-[23px] font-bold text-slate-800">
            {value}
          </h3>

          <span
            className={`mb-1 text-[8px] font-semibold ${changeClass}`}
          >
            {change}
          </span>

        </div>

      </div>


      <div
        className={`flex h-10 w-10 items-center justify-center rounded-md ${iconClass}`}
      >

        <Icon size={19} />

      </div>

    </div>
  );
}


/* =========================================================
   METRIC CARD
========================================================= */

function MetricCard({
  title,
  value,
  icon: Icon,
  iconClass,
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm">

      <div>

        <p className="text-[9px] text-slate-500">
          {title}
        </p>

        <p className="mt-1 text-[20px] font-bold text-slate-800">
          {value}
        </p>

      </div>


      <div
        className={`flex h-9 w-9 items-center justify-center rounded-md ${iconClass}`}
      >

        <Icon size={17} />

      </div>

    </div>
  );
}


/* =========================================================
   PLACEHOLDER PAGE
========================================================= */

function PlaceholderPage({ title, icon: Icon = FileText }) {
  return (
    <main className="flex min-h-[calc(100vh-70px)] items-center justify-center bg-[#f5f8fc] p-5">

      <div className="text-center">

        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-xl bg-blue-50 text-[#07539a]">

          <Icon size={28} />

        </div>

        <h2 className="mt-4 text-xl font-bold text-slate-800">
          {title}
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          This module will be available here.
        </p>

      </div>

    </main>
  );
}


/* =========================================================
   MAIN APPLICATION
========================================================= */

export default function App() {

  const { user, loading, logout, offline } = useAuth();

  /*
   * activeMenu controls which page is currently displayed.
   *
   * Dashboard
   * New Scan
   * Scan History
   * Reports
   * Admin Panel
   */

  const [activeMenu, setActiveMenu] = useState("Dashboard");

  // Wait for the initial "am I already logged in?" check, then show the
  // login screen if there's no authenticated user.
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f8fc] text-[11px] text-slate-400">
        Loading...
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }


  /* =======================================================
     SIDEBAR MENU
  ======================================================= */

  const allMenuItems = [
    {
      name: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "New Scan",
      icon: ScanLine,
    },
    {
      name: "Scan History",
      icon: History,
    },
    {
      name: "Reports",
      icon: FileText,
    },
    {
      name: "Admin Panel",
      icon: Users,
      adminOnly: true,
    },
  ];

  // Only admins see the Admin Panel link.
  const menuItems = allMenuItems.filter(
    (item) => !item.adminOnly || user.role === "admin"
  );


  /* =======================================================
     NAVIGATION FUNCTION
  ======================================================= */

  const handleNavigation = (page) => {
    setActiveMenu(page);
  };


  return (

    <div className="min-h-screen bg-[#f5f8fc]">

      {/* =====================================================
          SIDEBAR
      ===================================================== */}

      <aside className="fixed left-0 top-0 z-50 flex h-screen w-[205px] flex-col bg-[#062c57] text-white">

        {/* ===================================================
            LOGO
        =================================================== */}

        <div className="flex h-[70px] items-center gap-3 border-b border-white/10 px-5">

          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10">

            <ScanLine size={21} />

          </div>


          <div>

            <h1 className="text-[12px] font-bold tracking-wide">
              METROLOGY
            </h1>

            <p className="text-[9px] tracking-[2px] text-blue-200">
              SCANNER
            </p>

          </div>

        </div>


        {/* ===================================================
            NAVIGATION
        =================================================== */}

        <nav className="px-3 pt-5">

          {menuItems.map((item) => {

            const Icon = item.icon;

            const isActive =
              activeMenu === item.name;

            return (

              <button
                key={item.name}
                onClick={() =>
                  handleNavigation(item.name)
                }
                className={`mb-1.5 flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-[11px] transition ${
                  isActive
                    ? "bg-[#0d4e94] font-medium text-white shadow-sm"
                    : "text-blue-100 hover:bg-white/10"
                }`}
              >

                <Icon size={16} />

                <span>
                  {item.name}
                </span>

              </button>

            );

          })}

        </nav>


        {/* ===================================================
            SIDEBAR INSPECTOR PROFILE
        =================================================== */}

        <div className="mt-auto border-t border-white/10 p-4">

          <div className="flex items-center gap-2.5">

            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-300">

              <UserRound
                size={15}
                className="text-slate-600"
              />

            </div>


            <div>

              <p className="text-[10px] font-semibold">
                {user.name}
              </p>

              <div className="mt-0.5 flex items-center gap-1">

                <span className="h-1.5 w-1.5 rounded-full bg-green-400" />

                <span className="text-[8px] text-blue-100">
                  Online
                </span>

              </div>

            </div>

          </div>

          <button
            onClick={logout}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-md border border-white/15 py-2 text-[9px] font-semibold text-blue-100 transition hover:bg-white/10"
          >
            <LogOut size={13} />
            Sign Out
          </button>

        </div>

      </aside>


      {/* =====================================================
          MAIN CONTENT AREA
      ===================================================== */}

      <div className="ml-[205px] min-h-screen">

        {/* ===================================================
            TOP HEADER
        =================================================== */}

        <header className="flex h-[70px] items-center justify-between border-b border-slate-200 bg-white px-7">

          {/* Header Left */}

          <div>

            <h2 className="text-[16px] font-bold text-slate-800">

              {activeMenu === "Dashboard" &&
                `Welcome, ${user.name}`}

              {activeMenu === "New Scan" &&
                "New Product Inspection"}

              {activeMenu === "Scan History" &&
                "Scan History"}

              {activeMenu === "Reports" &&
                "Inspection Reports"}

              {activeMenu === "Admin Panel" &&
                "Administration Panel"}

            </h2>


            <p className="mt-1 text-[9px] text-slate-400">

              {activeMenu === "Dashboard" &&
                "Here's what's happening with your inspections today."}

              {activeMenu === "New Scan" &&
                "AI-powered product scanning and Legal Metrology compliance verification."}

              {activeMenu === "Scan History" &&
                "View and manage previously completed product inspections."}

              {activeMenu === "Reports" &&
                "Generate and manage inspection reports."}

              {activeMenu === "Admin Panel" &&
                "Manage inspectors, rules and system configuration."}

            </p>

          </div>


          {/* Header Right */}

          <div className="flex items-center gap-6">

            {/* ================================================
                SERVER OFFLINE BANNER
            ================================================== */}

            {offline && (
              <span className="flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[8px] font-semibold text-amber-600">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
                Server offline — reconnecting…
              </span>
            )}

            {/* ================================================
                NOTIFICATION
            ================================================== */}

            <button
              className="relative text-slate-500 transition hover:text-[#07539a]"
              title="Notifications"
            >

              <Bell size={18} />

              <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full border border-white bg-red-500" />

            </button>


            {/* =================================================
                PROFILE
            ================================================== */}

            <div className="flex cursor-pointer items-center gap-2">

              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200">

                <UserRound
                  size={15}
                  className="text-slate-600"
                />

              </div>


              <div>

                <p className="text-[10px] font-semibold text-slate-700">
                  {user.name}
                </p>

                <p className="text-[8px] capitalize text-slate-400">
                  {user.role}
                </p>

              </div>

              <button
                onClick={logout}
                title="Sign out"
                className="text-slate-400 transition hover:text-[#07539a]"
              >
                <LogOut size={14} />
              </button>

            </div>

          </div>

        </header>


        {/* ===================================================
            PAGE ROUTING
        =================================================== */}

        {activeMenu === "Dashboard" && (

          <Dashboard
            onNewScan={() =>
              handleNavigation("New Scan")
            }
          />

        )}


        {/* ===================================================
            NEW SCAN
        =================================================== */}

        {activeMenu === "New Scan" && (

          <NewScan />

        )}


        {/* ===================================================
            SCAN HISTORY
        =================================================== */}

        {activeMenu === "Scan History" && (

          <ScanHistory />

        )}


        {/* ===================================================
            REPORTS
        =================================================== */}

        {activeMenu === "Reports" && (
  <Reports />
)}


        {/* ===================================================
            ADMIN PANEL
        =================================================== */}

       {activeMenu === "Admin Panel" && (
  <AdminPanel />
)}

      </div>

    </div>
  );
}