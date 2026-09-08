import React, { useEffect, useState } from "react";
import {
  BarChart3,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Download,
  FileBarChart,
  FileText,
  Filter,
  Loader2,
  PieChart,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { dashboard as dashboardApi } from "../lib/api";
// dashboardApi.summaryReport downloads a real all-time PDF from the backend.

export default function Reports() {
  const [period, setPeriod] = useState("Daily");
  const [reportType, setReportType] = useState(
    "Inspection Summary"
  );
  const [status, setStatus] = useState("All");
  const [fromDate, setFromDate] = useState("2026-09-01");
  const [toDate, setToDate] = useState("2026-09-01");
  const [generating, setGenerating] = useState(false);

  const [statsData, setStatsData] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoadingStats(true);
    setStatsError("");

    dashboardApi
      .stats(period)
      .then((data) => {
        if (!cancelled) setStatsData(data);
      })
      .catch((err) => {
        if (!cancelled) setStatsError(err.message || "Failed to load report stats.");
      })
      .finally(() => {
        if (!cancelled) setLoadingStats(false);
      });

    return () => {
      cancelled = true;
    };
  }, [period]);

  const stats = {
    inspections: loadingStats ? "…" : (statsData?.total_inspections ?? 0).toLocaleString(),
    compliant: loadingStats ? "…" : (statsData?.compliant ?? 0).toLocaleString(),
    violations: loadingStats ? "…" : (statsData?.violations ?? 0).toLocaleString(),
    complianceRate: loadingStats ? "…" : `${statsData?.compliance_rate ?? 0}%`,
  };

  // Real donut proportions: backend returns total/compliant/violations.
  const totalAll = statsData?.total_inspections ?? 0;
  const passedPct = totalAll ? ((statsData?.compliant ?? 0) / totalAll) * 100 : 0;
  const failedPct = totalAll ? ((statsData?.violations ?? 0) / totalAll) * 100 : 0;
  const pendingPct = Math.max(0, 100 - passedPct - failedPct);
  const pendingCount = Math.max(0, totalAll - (statsData?.compliant ?? 0) - (statsData?.violations ?? 0));

  const violations = (statsData?.top_violations || []).map((v) => ({
    label: v.label,
    value: v.value,
    percentage: v.percentage,
  }));

  // Real PDF download: the backend compiles a summary report from live data.
  const generateReport = () => {
    setGenerating(true);
    dashboardApi
      .summaryReport()
      .catch((err) => alert(err.message || "Failed to generate report."))
      .finally(() => setGenerating(false));
  };

  const exportData = () => {
    const csv = [
      [
        "Category",
        "Count",
        "Percentage",
      ],
      [
        "Total Inspections",
        stats.inspections,
        "100%",
      ],
      [
        "Compliant",
        stats.compliant,
        stats.complianceRate,
      ],
      [
        "Violations",
        stats.violations,
        "",
      ],
      ...violations.map((item) => [
        item.label,
        item.value,
        item.percentage,
      ]),
    ];

    const content = csv
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([content], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "metrology-compliance-report.csv";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  return (
    <main className="min-h-[calc(100vh-70px)] bg-[#f5f8fc] p-5">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="mb-4 flex flex-col justify-between gap-3 xl:flex-row xl:items-center">

        <div>

          <div className="flex items-center gap-2">

            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-[#07539a]">
              <BarChart3 size={17} />
            </div>

            <div>

              <h1 className="text-[17px] font-bold text-slate-800">
                Reports & Compliance Analytics
              </h1>

              <p className="mt-0.5 text-[9px] text-slate-400">
                Analyze inspection performance and Legal Metrology compliance.
              </p>

            </div>

          </div>

        </div>


        {/* Period Selector */}

        <div className="flex w-fit items-center rounded-md border border-slate-200 bg-white p-0.5 shadow-sm">

          {["Daily", "Weekly", "Monthly"].map((item) => (

            <button
              key={item}
              onClick={() => setPeriod(item)}
              className={`rounded px-4 py-1.5 text-[8px] font-semibold transition ${
                period === item
                  ? "bg-[#07539a] text-white"
                  : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              {item}
            </button>

          ))}

        </div>

      </div>


      {/* =====================================================
          DATE FILTERS
      ===================================================== */}

      <section className="mb-3 rounded-lg border border-slate-200 bg-white p-3 shadow-sm">

        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">

          {/* From */}

          <div className="relative">

            <label className="absolute -top-1.5 left-2 z-10 bg-white px-1 text-[7px] text-slate-400">
              From Date
            </label>

            <div className="relative">

              <CalendarDays
                size={13}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />

              <input
                type="date"
                value={fromDate}
                onChange={(e) =>
                  setFromDate(e.target.value)
                }
                className="h-9 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
              />

            </div>

          </div>


          {/* To */}

          <div className="relative">

            <label className="absolute -top-1.5 left-2 z-10 bg-white px-1 text-[7px] text-slate-400">
              To Date
            </label>

            <div className="relative">

              <CalendarDays
                size={13}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />

              <input
                type="date"
                value={toDate}
                onChange={(e) =>
                  setToDate(e.target.value)
                }
                className="h-9 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
              />

            </div>

          </div>


          {/* Status */}

          <div className="relative">

            <label className="absolute -top-1.5 left-2 z-10 bg-white px-1 text-[7px] text-slate-400">
              Status
            </label>

            <div className="relative">

              <select
                value={status}
                onChange={(e) =>
                  setStatus(e.target.value)
                }
                className="h-9 w-full appearance-none rounded-md border border-slate-200 bg-white px-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
              >

                <option value="All">
                  All
                </option>

                <option value="Passed">
                  Passed
                </option>

                <option value="Failed">
                  Failed
                </option>

                <option value="Pending Review">
                  Pending Review
                </option>

              </select>

              <ChevronDown
                size={13}
                className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
              />

            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          KPI CARDS
      ===================================================== */}

      <section className="grid grid-cols-1 gap-3 md:grid-cols-3">

        {/* Total */}

        <AnalyticsCard
          title="Total Inspections"
          value={stats.inspections}
          icon={FileText}
          iconClass="bg-blue-50 text-blue-600"
          subtitle={`${period} inspections`}
        />


        {/* Compliant */}

        <AnalyticsCard
          title="Compliant"
          value={stats.compliant}
          icon={CheckCircle2}
          iconClass="bg-green-50 text-green-600"
          subtitle={`${stats.complianceRate} compliance rate`}
        />


        {/* Violations */}

        <AnalyticsCard
          title="Violations"
          value={stats.violations}
          icon={XCircle}
          iconClass="bg-red-50 text-red-600"
          subtitle="Issues detected"
        />

      </section>


      {/* =====================================================
          ANALYTICS AREA
      ===================================================== */}

      <section className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-[1fr_1.15fr]">

        {/* ===================================================
            COMPLIANCE OVERVIEW
        =================================================== */}

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">

          <div className="flex items-center justify-between">

            <div>

              <h2 className="text-[11px] font-bold text-slate-700">
                Compliance Overview
              </h2>

              <p className="mt-0.5 text-[8px] text-slate-400">
                Inspection outcome distribution
              </p>

            </div>

            <PieChart
              size={16}
              className="text-slate-400"
            />

          </div>


          <div className="mt-5 flex items-center justify-center gap-8">

            {/* Donut - real proportions from the backend */}

            <div
              className="relative flex h-32 w-32 items-center justify-center rounded-full"
              style={{
                background: `conic-gradient(#16a34a 0% ${passedPct}%, #dc2626 ${passedPct}% ${passedPct + failedPct}%, #f59e0b ${passedPct + failedPct}% 100%)`,
              }}
            >

              <div className="flex h-[82px] w-[82px] flex-col items-center justify-center rounded-full bg-white">

                <span className="text-[19px] font-bold text-slate-800">
                  {stats.complianceRate}
                </span>

                <span className="text-[7px] text-slate-400">
                  Overall
                </span>

              </div>

            </div>


            {/* Legend */}

            <div className="space-y-3">

              <Legend
                color="bg-green-500"
                label="Passed"
                value={stats.compliant}
                percentage={stats.complianceRate}
              />

              <Legend
                color="bg-red-500"
                label="Violations"
                value={stats.violations}
                percentage={`${Math.round(failedPct)}%`}
              />

              <Legend
                color="bg-orange-400"
                label="Pending Review"
                value={pendingCount}
                percentage={`${Math.round(pendingPct)}%`}
              />

            </div>

          </div>

        </div>


        {/* ===================================================
            VIOLATION ANALYSIS
        =================================================== */}

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">

          <div className="flex items-center justify-between">

            <div>

              <h2 className="text-[11px] font-bold text-slate-700">
                Violation Analysis (Top 5)
              </h2>

              <p className="mt-0.5 text-[8px] text-slate-400">
                Most frequently detected compliance issues
              </p>

            </div>

            <BarChart3
              size={16}
              className="text-slate-400"
            />

          </div>


          <div className="mt-4 space-y-3">

            {violations.map((item, index) => (

              <div key={item.label}>

                <div className="mb-1 flex items-center justify-between">

                  <span className="text-[8px] font-medium text-slate-600">
                    {item.label}
                  </span>

                  <span className="text-[8px] font-bold text-slate-600">
                    {item.value}
                  </span>

                </div>


                <div className="h-[6px] overflow-hidden rounded-full bg-slate-100">

                  <div
                    className={`h-full rounded-full ${
                      index === 0
                        ? "bg-red-500"
                        : index === 1
                        ? "bg-red-400"
                        : "bg-orange-400"
                    }`}
                    style={{
                      width: `${Math.max(18, parseFloat(item.percentage) || 0)}%`,
                    }}
                  />

                </div>

              </div>

            ))}

          </div>

        </div>

      </section>


      {/* =====================================================
          GENERATE REPORT
      ===================================================== */}

      <section className="mt-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">

        <div className="flex items-center gap-2">

          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-50 text-[#07539a]">

            <FileBarChart size={16} />

          </div>

          <div>

            <h2 className="text-[11px] font-bold text-slate-700">
              Generate Report
            </h2>

            <p className="text-[8px] text-slate-400">
              Create an official inspection analytics report.
            </p>

          </div>

        </div>


        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">

          {/* Report Type */}

          <div>

            <label className="mb-1.5 block text-[8px] font-semibold text-slate-500">
              Report Type
            </label>

            <select
              value={reportType}
              onChange={(e) =>
                setReportType(e.target.value)
              }
              className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
            >

              <option>
                Inspection Summary
              </option>

              <option>
                Compliance Analytics
              </option>

              <option>
                Violation Analysis
              </option>

              <option>
                Inspector Performance
              </option>

            </select>

          </div>


          {/* Date Range */}

          <div>

            <label className="mb-1.5 block text-[8px] font-semibold text-slate-500">
              Date Range
            </label>

            <div className="flex items-center gap-2">

              <input
                type="date"
                value={fromDate}
                onChange={(e) =>
                  setFromDate(e.target.value)
                }
                className="h-9 min-w-0 flex-1 rounded-md border border-slate-200 px-2 text-[8px] text-slate-600 outline-none focus:border-blue-400"
              />

              <span className="text-[8px] text-slate-400">
                to
              </span>

              <input
                type="date"
                value={toDate}
                onChange={(e) =>
                  setToDate(e.target.value)
                }
                className="h-9 min-w-0 flex-1 rounded-md border border-slate-200 px-2 text-[8px] text-slate-600 outline-none focus:border-blue-400"
              />

            </div>

          </div>


          {/* Status */}

          <div>

            <label className="mb-1.5 block text-[8px] font-semibold text-slate-500">
              Status
            </label>

            <select
              value={status}
              onChange={(e) =>
                setStatus(e.target.value)
              }
              className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
            >

              <option>
                All
              </option>

              <option>
                Passed
              </option>

              <option>
                Failed
              </option>

              <option>
                Pending Review
              </option>

            </select>

          </div>

        </div>


        {/* Buttons */}

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">

          <button
            onClick={generateReport}
            disabled={generating}
            className="flex h-9 items-center justify-center gap-2 rounded-md bg-[#07539a] px-5 text-[9px] font-semibold text-white transition hover:bg-[#06447f] disabled:cursor-not-allowed disabled:opacity-60"
          >

            {generating ? (
              <>
                <Loader2
                  size={13}
                  className="animate-spin"
                />

                GENERATING...

              </>
            ) : (
              <>
                <FileText size={13} />

                GENERATE PDF REPORT

              </>
            )}

          </button>


          <button
            onClick={exportData}
            className="flex h-9 items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-5 text-[9px] font-semibold text-slate-600 transition hover:bg-slate-50"
          >

            <Download size={13} />

            EXPORT DATA

          </button>


          <button
            onClick={() => window.location.reload()}
            className="flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-4 text-[9px] font-semibold text-slate-500 hover:bg-slate-100"
          >

            <RefreshCw size={12} />

            REFRESH

          </button>

        </div>

      </section>


      {/* =====================================================
          ANALYTICS FOOTER
      ===================================================== */}

      <div className="mt-3 flex flex-col justify-between gap-1 px-1 sm:flex-row">

        <p className="text-[8px] text-slate-400">
          Analytics period:{" "}
          <span className="font-semibold text-slate-500">
            {period}
          </span>
        </p>

        <p className="text-[8px] text-slate-400">
          AI Compliance Engine • Legal Metrology Rules v2.4
        </p>

      </div>

    </main>
  );
}


/* ============================================================
   ANALYTICS CARD
============================================================ */

function AnalyticsCard({
  title,
  value,
  icon: Icon,
  iconClass,
  subtitle,
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-sm">

      <div>

        <p className="text-[9px] font-medium text-slate-500">
          {title}
        </p>

        <p className="mt-1 text-[22px] font-bold text-slate-800">
          {value}
        </p>

        <p className="mt-1 text-[8px] text-slate-400">
          {subtitle}
        </p>

      </div>


      <div
        className={`flex h-10 w-10 items-center justify-center rounded-lg ${iconClass}`}
      >

        <Icon size={19} />

      </div>

    </div>
  );
}


/* ============================================================
   LEGEND
============================================================ */

function Legend({
  color,
  label,
  value,
  percentage,
}) {
  return (
    <div className="flex items-center gap-2">

      <span
        className={`h-2.5 w-2.5 rounded-sm ${color}`}
      />

      <div>

        <div className="flex items-center gap-2">

          <span className="text-[8px] font-medium text-slate-600">
            {label}
          </span>

          <span className="text-[8px] font-bold text-slate-700">
            {value}
          </span>

        </div>

        <span className="text-[7px] text-slate-400">
          {percentage}
        </span>

      </div>

    </div>
  );
}