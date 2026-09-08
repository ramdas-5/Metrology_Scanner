import React, { useEffect, useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  Filter,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { scans as scansApi } from "../lib/api";

const PAGE_SIZE = 10;

function formatDateTime(iso) {
  if (!iso) return "--";
  try {
    return new Date(iso).toLocaleString("en-IN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function ScanHistory() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const [scanList, setScanList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [selectedScan, setSelectedScan] = useState(null);
  const [selectedLoading, setSelectedLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState(null);

  const fetchScans = async () => {
    setLoading(true);
    setLoadError("");
    try {
      const data = await scansApi.list({
        status: status !== "All" ? status : undefined,
        search: search || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        page: currentPage,
        page_size: PAGE_SIZE,
      });
      setScanList(data);
    } catch (err) {
      setLoadError(err.message || "Failed to load scan history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

  // Live search: re-query the backend whenever a filter changes.
  useEffect(() => {
    const t = setTimeout(() => {
      setCurrentPage(1);
      fetchScans();
    }, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, status, fromDate, toDate]);

  const filteredScans = scanList;

  const resetFilters = () => {
    setSearch("");
    setStatus("All");
    setFromDate("");
    setToDate("");
    setCurrentPage(1);
  };

  const handleView = async (scan) => {
    setSelectedScan(scan);
    setSelectedLoading(true);
    try {
      const full = await scansApi.get(scan.id);
      setSelectedScan(full);
    } catch (err) {
      setSelectedScan({ ...scan, error: err.message });
    } finally {
      setSelectedLoading(false);
    }
  };

  const handleDownload = async (scanId) => {
    setDownloadingId(scanId);
    try {
      await scansApi.downloadReport(scanId, `compliance_report_${scanId}.pdf`);
    } catch (err) {
      alert(err.message || "Could not generate report.");
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <main className="min-h-[calc(100vh-70px)] bg-[#f5f8fc] p-5">

      {/* =====================================================
          PAGE HEADER
      ====================================================== */}

      <div className="mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-[#07539a]">
            <SlidersHorizontal size={17} />
          </div>
          <div>
            <h1 className="text-[17px] font-bold text-slate-800">
              Scan History
            </h1>
            <p className="mt-0.5 text-[9px] text-slate-400">
              View and manage previously completed product inspections.
            </p>
          </div>
        </div>
      </div>

      {/* =====================================================
          FILTER BAR
      ====================================================== */}

      <section className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
        <div className="grid grid-cols-1 gap-2 md:grid-cols-[1.5fr_0.8fr_0.8fr_0.8fr_auto]">

          {/* Search */}
          <div className="relative">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search by product, MRP, inspector..."
              className="h-9 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-[9px] text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-50"
            />
          </div>

          {/* Status */}
          <div className="relative">
            <label className="absolute -top-1.5 left-2 bg-white px-1 text-[7px] text-slate-400">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setCurrentPage(1);
              }}
              className="h-9 w-full appearance-none rounded-md border border-slate-200 bg-white px-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
            >
              <option>All</option>
              <option>Passed</option>
              <option>Failed</option>
              <option>Pending Review</option>
            </select>
          </div>

          {/* From */}
          <div className="relative">
            <label className="absolute -top-1.5 left-2 bg-white px-1 text-[7px] text-slate-400">
              From
            </label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
            />
          </div>

          {/* To */}
          <div className="relative">
            <label className="absolute -top-1.5 left-2 bg-white px-1 text-[7px] text-slate-400">
              To
            </label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-[9px] text-slate-600 outline-none focus:border-blue-400"
            />
          </div>

          {/* Filter */}
          <button
            onClick={() => {
              setCurrentPage(1);
              fetchScans();
            }}
            className="flex h-9 items-center justify-center gap-1.5 rounded-md bg-[#07539a] px-4 text-[9px] font-semibold text-white transition hover:bg-[#06447f]"
          >
            <Filter size={13} />
            Filter
          </button>
        </div>

        {/* Reset */}
        {(search || status !== "All" || fromDate || toDate) && (
          <button
            onClick={resetFilters}
            className="mt-2 text-[8px] font-medium text-[#07539a] hover:underline"
          >
            Clear filters
          </button>
        )}
      </section>

      {/* =====================================================
          TABLE
      ====================================================== */}

      <section className="mt-3 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-[#f8fafc]">
                <TableHead>S.No</TableHead>
                <TableHead>Product</TableHead>
                <TableHead>MRP (₹)</TableHead>
                <TableHead>Mfg. / Pkg. Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Inspected By</TableHead>
                <TableHead>Inspected On</TableHead>
                <TableHead align="right">Action</TableHead>
              </tr>
            </thead>

            <tbody>
              {!loading && !loadError && filteredScans.map((scan, index) => (
                <tr
                  key={scan.id}
                  className="border-b border-slate-100 transition hover:bg-blue-50/30"
                >
                  <td className="px-4 py-3 text-[9px] text-slate-500">
                    {(currentPage - 1) * PAGE_SIZE + index + 1}
                  </td>

                  <td className="px-4 py-3">
                    <p className="text-[9px] font-semibold text-slate-700">
                      {scan.product_name || "Unidentified Product"}
                    </p>
                  </td>

                  <td className="px-4 py-3 text-[9px] font-medium text-slate-700">
                    {scan.mrp || "--"}
                  </td>

                  <td className="px-4 py-3 text-[9px] text-slate-600">
                    {scan.mfg_date || "N/A"}
                  </td>

                  <td className="px-4 py-3">
                    <StatusBadge status={scan.status} />
                  </td>

                  {/* NEW: the inspector who performed this scan */}
                  <td className="px-4 py-3">
                    <p className="text-[9px] font-medium text-slate-700">
                      {scan.inspector_name || "—"}
                    </p>
                    {scan.inspector_email && (
                      <p className="text-[7px] text-slate-400">
                        {scan.inspector_email}
                      </p>
                    )}
                  </td>

                  <td className="px-4 py-3 text-[9px] text-slate-500">
                    {formatDateTime(scan.created_at)}
                  </td>

                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => handleView(scan)}
                        className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-white px-3 py-1.5 text-[8px] font-semibold text-[#07539a] transition hover:bg-blue-50"
                      >
                        <Eye size={12} />
                        View
                      </button>
                      <button
                        onClick={() => handleDownload(scan.id)}
                        disabled={downloadingId === scan.id}
                        className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-[8px] font-semibold text-slate-500 transition hover:bg-slate-50 disabled:opacity-50"
                        title="Download PDF report"
                      >
                        <Download size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {/* Loading state */}
              {loading && (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-[9px] text-slate-400">
                    Loading scan history...
                  </td>
                </tr>
              )}

              {/* Error state */}
              {!loading && loadError && (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-[9px] text-red-500">
                    {loadError}
                  </td>
                </tr>
              )}

              {/* Empty state */}
              {!loading && !loadError && filteredScans.length === 0 && (
                <tr>
                  <td colSpan="8" className="py-12 text-center">
                    <Search size={25} className="mx-auto text-slate-300" />
                    <p className="mt-2 text-[10px] font-semibold text-slate-500">
                      No inspections found
                    </p>
                    <p className="mt-1 text-[8px] text-slate-400">
                      Try changing your search or filters.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* =================================================
            TABLE FOOTER
        ================================================== */}

        <div className="flex flex-col gap-3 border-t border-slate-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[8px] text-slate-400">
            Page{" "}
            <span className="font-semibold text-slate-600">{currentPage}</span>{" "}
            •{" "}
            <span className="font-semibold text-slate-600">
              {filteredScans.length}
            </span>{" "}
            entries shown
          </p>

          {/* Pagination */}
          <div className="flex items-center gap-1">
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="flex h-7 w-7 items-center justify-center rounded border border-slate-200 text-slate-400 hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronLeft size={13} />
            </button>
            <PageButton active>{currentPage}</PageButton>
            <button
              disabled={filteredScans.length < PAGE_SIZE}
              onClick={() => setCurrentPage((p) => p + 1)}
              className="flex h-7 w-7 items-center justify-center rounded border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronRight size={13} />
            </button>
          </div>
        </div>
      </section>

      {/* =====================================================
          VIEW MODAL
      ====================================================== */}

      {selectedScan && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
          onClick={() => setSelectedScan(null)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-xl bg-white p-5 shadow-2xl"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[8px] font-semibold uppercase tracking-wider text-blue-500">
                  Inspection Details
                </p>
                <h2 className="mt-1 text-[15px] font-bold text-slate-800">
                  {selectedScan.product_name || "Unidentified Product"}
                </h2>
              </div>
              <StatusBadge status={selectedScan.status} />
            </div>

            {selectedLoading && (
              <p className="mt-3 text-[9px] text-slate-400">Loading full details...</p>
            )}

            <div className="mt-5 grid grid-cols-2 gap-3">
              <Detail
                label="MRP"
                value={selectedScan.mrp ? `₹${selectedScan.mrp}` : "Not detected"}
              />
              <Detail
                label="Mfg. / Pkg. Date"
                value={selectedScan.mfg_date || "N/A"}
              />
              <Detail
                label="Net Quantity"
                value={selectedScan.net_quantity || "Not detected"}
              />
              <Detail
                label="Manufacturer"
                value={selectedScan.manufacturer || "Not detected"}
              />
              <Detail
                label="Consumer Care"
                value={selectedScan.consumer_care || "Not detected"}
              />
              <Detail
                label="Inspected On"
                value={formatDateTime(selectedScan.created_at)}
              />
              <Detail
                label="Inspected By"
                value={selectedScan.inspector_name || "—"}
              />
              <Detail
                label="Inspector Email"
                value={selectedScan.inspector_email || "—"}
              />
            </div>

            <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-3">
              <p className="text-[8px] font-semibold text-blue-700">
                AI + OCR Result
              </p>
              <p className="mt-1 text-[9px] leading-4 text-blue-600">
                Compliance score: {selectedScan.compliance_score ?? "--"}% •{" "}
                AI label classifier: {selectedScan.label_classifier_result || "--"}
                {selectedScan.label_classifier_confidence
                  ? ` (${selectedScan.label_classifier_confidence}%)`
                  : ""}
              </p>

              {(selectedScan.ocr_engine || selectedScan.ai_used || selectedScan.ai_report) && (
                <div className="mt-2 border-t border-blue-100 pt-2">
                  <p className="text-[7px] font-medium text-blue-500">
                    OCR engine: {(selectedScan.ocr_engine || "tesseract").toUpperCase()}{" "}
                    • Result source:{" "}
                    {selectedScan.ai_used
                      ? `AI (${selectedScan.ai_model || "OpenRouter"})`
                      : "Rule engine / regex"}
                  </p>

                  {selectedScan.ai_report && (
                    <p className="mt-2 max-h-36 overflow-y-auto whitespace-pre-wrap rounded-md bg-white p-2.5 text-[8px] leading-4 text-slate-600">
                      {selectedScan.ai_report}
                    </p>
                  )}
                </div>
              )}
            </div>

            {selectedScan.violations && selectedScan.violations.length > 0 && (
              <div className="mt-3 space-y-1.5">
                <p className="text-[8px] font-semibold text-red-600">
                  {selectedScan.violations.length} Violation(s)
                </p>
                {selectedScan.violations.map((v) => (
                  <div key={v.id} className="rounded-md border border-red-100 bg-red-50/50 px-2.5 py-1.5 text-[8px] text-slate-600">
                    {v.label} <span className="text-slate-400">({v.rule_reference})</span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 grid grid-cols-2 gap-2">
              <button
                onClick={() => setSelectedScan(null)}
                className="h-9 rounded-md border border-slate-300 text-[9px] font-semibold text-slate-600 hover:bg-slate-50"
              >
                CLOSE
              </button>
              <button
                onClick={() => handleDownload(selectedScan.id)}
                disabled={downloadingId === selectedScan.id}
                className="flex h-9 items-center justify-center gap-1.5 rounded-md bg-[#07539a] text-[9px] font-semibold text-white hover:bg-[#06447f] disabled:opacity-50"
              >
                <Download size={13} />
                {downloadingId === selectedScan.id ? "Generating..." : "Download Report"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

/* ============================================================
   TABLE HEAD
============================================================ */

function TableHead({ children, align = "left" }) {
  return (
    <th
      className={`px-4 py-3 text-[8px] font-semibold uppercase tracking-wide text-slate-500 ${
        align === "right" ? "text-right" : "text-left"
      }`}
    >
      {children}
    </th>
  );
}

/* ============================================================
   STATUS BADGE
============================================================ */

function StatusBadge({ status }) {
  const styles = {
    Passed: "bg-green-50 text-green-600 border-green-100",
    Failed: "bg-red-50 text-red-600 border-red-100",
    "Pending Review": "bg-orange-50 text-orange-600 border-orange-100",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[7px] font-semibold ${styles[status] || "bg-slate-50 text-slate-600 border-slate-200"}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          status === "Passed"
            ? "bg-green-500"
            : status === "Failed"
            ? "bg-red-500"
            : "bg-orange-500"
        }`}
      />
      {status}
    </span>
  );
}

/* ============================================================
   PAGE BUTTON
============================================================ */

function PageButton({ children, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex h-7 min-w-7 items-center justify-center rounded border px-2 text-[8px] font-semibold ${
        active
          ? "border-[#07539a] bg-[#07539a] text-white"
          : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
      }`}
    >
      {children}
    </button>
  );
}

/* ============================================================
   DETAIL
============================================================ */

function Detail({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <p className="text-[7px] text-slate-400">{label}</p>
      <p className="mt-1 text-[9px] font-semibold text-slate-700">{value}</p>
    </div>
  );
}
