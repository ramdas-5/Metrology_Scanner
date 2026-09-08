import React, { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  ChevronDown,
  Database,
  Download,
  FileText,
  Layers,
  RefreshCw,
  ScanLine,
  ShieldCheck,
  Trash2,
  Upload,
  X,
  Zap,
} from "lucide-react";
import { scans as scansApi } from "../lib/api";

export default function NewScan() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);

  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [scanning, setScanning] = useState(false);

  // ---- Multi-side capture state ----
  // Each side: { id, preview (dataURL/objectURL), blob, source: "camera"|"upload" }
  const [sides, setSides] = useState([]);
  const [activeSide, setActiveSide] = useState(null); // preview shown in the viewport

  const [productName, setProductName] = useState("");
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState("");
  const [downloadingReport, setDownloadingReport] = useState(false);

  // =========================================================
  // START CAMERA
  // =========================================================

  const startCamera = async () => {
    try {
      setCameraError("");

      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError("Camera access is not supported by this browser.");
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraActive(true);
      }
    } catch (error) {
      console.error(error);
      setCameraError("Camera permission was denied or the camera is unavailable.");
      setCameraActive(false);
    }
  };

  // =========================================================
  // STOP CAMERA
  // =========================================================

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    startCamera();
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // =========================================================
  // ADD A SIDE (camera capture or upload) - NO auto-scan
  // =========================================================

  const blobToDataUrl = (blob) =>
    new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });

  const addSide = async (blob, source) => {
    const preview = await blobToDataUrl(blob);
    const side = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      preview,
      blob,
      source,
    };
    setSides((prev) => [...prev, side]);
    setActiveSide(side.preview);
    setScanResult(null);
    setScanError("");
  };

  const handleCapture = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((resolve) =>
      canvas.toBlob((b) => resolve(b), "image/jpeg", 0.9)
    );
    if (blob) await addSide(blob, "camera");
  };

  const handleFilesSelected = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    for (const file of files) {
      await addSide(file, "upload");
    }
    // Allow re-selecting the same files later.
    event.target.value = "";
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const removeSide = (id) => {
    setSides((prev) => {
      const next = prev.filter((s) => s.id !== id);
      if (next.length === 0) setActiveSide(null);
      else if (activeSide && prev.find((s) => s.id === id)?.preview === activeSide)
        setActiveSide(next[next.length - 1].preview);
      return next;
    });
    setScanResult(null);
  };

  const clearAllSides = () => {
    setSides([]);
    setActiveSide(null);
    setScanResult(null);
    setScanError("");
  };

  // =========================================================
  // SCAN BUTTON - send ALL captured sides in ONE request
  // =========================================================

  const handleScan = async () => {
    if (!sides.length) return;
    setScanning(true);
    setScanError("");
    setScanResult(null);
    try {
      const result = await scansApi.createMulti(
        sides.map((s) => s.blob),
        productName || undefined
      );
      setScanResult(result);
    } catch (err) {
      setScanError(err.message || "Scan failed. Please try again.");
    } finally {
      setScanning(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!scanResult) return;
    setDownloadingReport(true);
    try {
      await scansApi.downloadReport(
        scanResult.id,
        `compliance_report_${scanResult.id}.pdf`
      );
    } catch (err) {
      setScanError(err.message || "Could not generate report.");
    } finally {
      setDownloadingReport(false);
    }
  };

  const hasResult = !!scanResult;

  return (
    <div className="min-h-[calc(100vh-70px)] bg-[#f5f8fc] p-5">

      {/* ====================================================
          HEADER
      ===================================================== */}

      <div className="mb-4 flex items-center justify-between">

        <div>
          <div className="flex items-center gap-2">
            <ScanLine size={20} className="text-[#07539a]" />
            <h1 className="text-[18px] font-bold text-slate-800">
              New Product Scan
            </h1>
          </div>
          <p className="mt-1 text-[10px] text-slate-400">
            Capture or upload every side of the package, then press SCAN ONCE.
          </p>
        </div>

        <div className="flex items-center gap-3">

          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="Product name (optional)"
            className="h-8 w-[190px] rounded-md border border-slate-300 px-3 text-[10px] outline-none placeholder:text-slate-300 focus:border-[#07539a]"
          />

          <div className="flex items-center gap-2 rounded-full border border-green-200 bg-green-50 px-3 py-1.5">
            <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
            <span className="text-[9px] font-semibold text-green-700">
              {cameraActive ? "Camera Ready" : "Camera Offline"}
            </span>
          </div>

        </div>

      </div>

      {scanError && (
        <div className="mb-4 flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-[10px] font-medium text-red-600">
          <AlertTriangle size={14} />
          {scanError}
        </div>
      )}

      {/* ====================================================
          MAIN CONTENT
      ===================================================== */}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.05fr_0.95fr]">

        {/* ==================================================
            CAPTURE PANEL
        =================================================== */}

        <section className="overflow-hidden rounded-xl border border-slate-200 bg-[#0b1117] shadow-sm">

          {/* Panel Header */}
          <div className="flex h-[48px] items-center justify-between border-b border-white/10 px-4">

            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  cameraActive ? "bg-red-500 animate-pulse" : "bg-slate-500"
                }`}
              />
              <span className="text-[11px] font-semibold text-white">
                {activeSide ? "REVIEW" : cameraActive ? "REC" : "CAMERA"}
              </span>
            </div>

            <div className="flex items-center gap-2 text-slate-300">
              <Layers size={15} />
              <span className="text-[9px]">
                {sides.length} side{sides.length === 1 ? "" : "s"} captured
              </span>
            </div>

          </div>

          {/* ==================================================
              VIEWPORT: live video when nothing captured yet,
              otherwise the selected side's preview
          ================================================== */}

          <div className="relative h-[400px] overflow-hidden bg-black">

            <video
              ref={videoRef}
              muted
              playsInline
              className={`absolute inset-0 h-full w-full object-cover ${
                activeSide ? "opacity-0" : "opacity-100"
              }`}
            />

            {activeSide && (
              <img
                src={activeSide}
                alt="Captured side"
                className="absolute inset-0 h-full w-full object-cover"
              />
            )}

            {cameraError && !activeSide && (
              <div className="absolute inset-0 flex items-center justify-center bg-[#101820] px-8 text-center">
                <div>
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-400">
                    <Camera size={22} />
                  </div>
                  <p className="text-[11px] font-semibold text-white">
                    Camera Access Required
                  </p>
                  <p className="mx-auto mt-2 max-w-[280px] text-[9px] leading-4 text-slate-400">
                    {cameraError}
                  </p>
                  <button
                    onClick={startCamera}
                    className="mt-4 rounded-md bg-[#07539a] px-4 py-2 text-[9px] font-semibold text-white hover:bg-[#0866b7]"
                  >
                    ENABLE CAMERA
                  </button>
                </div>
              </div>
            )}

            {/* Scan line while analyzing */}
            {scanning && (
              <div className="absolute left-0 right-0 top-1/2 h-[2px] animate-pulse bg-cyan-300 shadow-[0_0_20px_8px_rgba(0,210,255,.5)]" />
            )}

            {/* Instruction + buttons */}
            <div className="absolute bottom-0 left-0 right-0 bg-black/70 p-4 backdrop-blur">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[10px] font-semibold text-white">
                    {scanning
                      ? `Analyzing ${sides.length} side${sides.length === 1 ? "" : "s"} with OCR + AI...`
                      : activeSide
                      ? "Side captured. Add more sides or press SCAN."
                      : "Place one side of the product label inside the frame."}
                  </p>
                  <p className="mt-1 text-[8px] text-slate-300">
                    Capture front, back, sides — all declarations across every side are checked together.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleUploadClick}
                    disabled={scanning}
                    className="flex h-10 items-center justify-center gap-2 rounded-md border border-white/40 bg-white/10 px-3 text-[9px] font-bold text-white backdrop-blur transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-50"
                    title="Upload image files (JPG/PNG/WebP) - multiple allowed"
                  >
                    <Upload size={14} />
                    UPLOAD
                  </button>

                  <button
                    onClick={handleCapture}
                    disabled={!cameraActive || scanning}
                    className="flex h-10 min-w-[105px] items-center justify-center gap-2 rounded-md bg-[#07539a] px-4 text-[10px] font-bold text-white transition hover:bg-[#0866b7] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Camera size={16} />
                    ADD SIDE
                  </button>

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleFilesSelected}
                    className="hidden"
                  />
                </div>
              </div>
            </div>

          </div>

          {/* ==================================================
              SIDE THUMBNAILS
          ================================================== */}

          <div className="border-t border-white/10 bg-[#101820] px-4 py-3">
            {sides.length === 0 ? (
              <p className="text-center text-[8px] text-slate-500">
                No sides captured yet — take a photo of each side or upload images.
              </p>
            ) : (
              <div className="flex flex-wrap items-center gap-2">
                {sides.map((side, i) => (
                  <div
                    key={side.id}
                    className={`group relative h-16 w-16 overflow-hidden rounded-md border-2 ${
                      activeSide === side.preview
                        ? "border-cyan-400"
                        : "border-white/20"
                    }`}
                  >
                    <img
                      src={side.preview}
                      alt={`Side ${i + 1}`}
                      className="h-full w-full object-cover"
                      onClick={() => setActiveSide(side.preview)}
                    />
                    <span className="absolute left-1 top-1 rounded bg-black/60 px-1 text-[7px] font-bold text-white">
                      {i + 1}
                    </span>
                    <button
                      onClick={() => removeSide(side.id)}
                      disabled={scanning}
                      title="Remove this side"
                      className="absolute right-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-black/60 text-white opacity-0 transition group-hover:opacity-100 hover:bg-red-500 disabled:opacity-0"
                    >
                      <X size={10} />
                    </button>
                    <span className="absolute bottom-0 left-0 right-0 bg-black/60 px-1 text-center text-[6px] uppercase text-slate-300">
                      {side.source}
                    </span>
                  </div>
                ))}

                <button
                  onClick={clearAllSides}
                  disabled={scanning}
                  className="flex h-16 items-center gap-1 rounded-md border border-white/20 px-2 text-[7px] font-semibold text-slate-300 transition hover:border-red-400 hover:text-red-400 disabled:opacity-50"
                >
                  <Trash2 size={12} />
                  CLEAR
                </button>
              </div>
            )}
          </div>

          {/* ==================================================
              THE SCAN BUTTON
          ================================================== */}

          <div className="bg-[#0b1117] px-4 pb-4">
            <button
              onClick={handleScan}
              disabled={!sides.length || scanning}
              className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-gradient-to-r from-[#07539a] to-[#0a6dc0] text-[12px] font-bold tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {scanning ? (
                <>
                  <RefreshCw size={17} className="animate-spin" />
                  ANALYZING {sides.length} SIDE{sides.length === 1 ? "" : "S"}...
                </>
              ) : (
                <>
                  <Zap size={17} />
                  SCAN {sides.length > 0 ? `${sides.length} SIDE${sides.length === 1 ? "" : "S"}` : ""}
                </>
              )}
            </button>
            <p className="mt-2 text-center text-[7px] text-slate-500">
              One scan checks every captured side together — fastest way to a complete result.
            </p>
          </div>

        </section>

        {/* ==================================================
            AI OCR RESULTS
        ================================================== */}

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-[#07539a]">
                <ScanLine size={19} />
              </div>
              <div>
                <h2 className="text-[14px] font-bold text-slate-800">
                  AI Vision + OCR Analysis
                </h2>
                <p className="text-[8px] text-slate-400">
                  Combined result from all captured sides
                </p>
              </div>
            </div>

            {hasResult && (
              <div className="flex flex-col items-end gap-1.5">
                <span
                  className={`flex items-center gap-1 rounded-full px-2 py-1 text-[8px] font-semibold ${
                    scanResult.status === "Passed"
                      ? "bg-green-50 text-green-600"
                      : scanResult.status === "Failed"
                      ? "bg-red-50 text-red-600"
                      : "bg-amber-50 text-amber-600"
                  }`}
                >
                  <CheckCircle2 size={11} />
                  {scanResult.status}
                </span>
                {scanResult.cached && (
                  <span className="flex items-center gap-1 rounded-full border border-purple-200 bg-purple-50 px-2 py-1 text-[8px] font-semibold text-purple-600">
                    <Database size={11} />
                    From cache • {scanResult.similarity ?? ""}% similar
                  </span>
                )}
              </div>
            )}
          </div>

          {/* OCR Fields */}
          <div className="space-y-2.5">
            <OCRField
              label="MRP (₹)"
              value={scanResult?.mrp || (hasResult ? "Not detected" : "--")}
            />
            <OCRField
              label="Net Quantity"
              value={scanResult?.net_quantity || (hasResult ? "Not detected" : "--")}
            />
            <OCRField
              label="Manufacturer"
              value={scanResult?.manufacturer || (hasResult ? "Not detected" : "--")}
            />
            <OCRField
              label="Mfg. / Pkg. Date"
              value={scanResult?.mfg_date || (hasResult ? "Not detected" : "--")}
            />
            <OCRField
              label="Consumer Info"
              value={scanResult?.consumer_care || (hasResult ? "Not detected" : "--")}
            />
            <OCRField
              label="AI Label Classifier"
              value={
                scanResult?.label_classifier_result
                  ? `${scanResult.label_classifier_result} (${scanResult.label_classifier_confidence}%)`
                  : "--"
              }
            />
          </div>

          {/* AI Pipeline Meta + Report */}
          {hasResult && (
            <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50/60 p-3.5">
              <div className="flex items-center justify-between">
                <p className="text-[8px] font-bold text-blue-700">AI Analysis</p>
                <p className="text-[7px] text-slate-400">
                  OCR: {(scanResult.ocr_engine || "tesseract").toUpperCase()} • Source:{" "}
                  {scanResult.ai_used
                    ? `AI (${scanResult.ai_model || "OpenRouter"})`
                    : "Rule engine (no AI key)"}
                </p>
              </div>

              {scanResult.ai_report && (
                <details className="group mt-2">
                  <summary className="flex cursor-pointer items-center justify-between text-[8px] font-semibold text-[#07539a]">
                    Read the AI inspection report
                    <ChevronDown size={12} className="transition group-open:rotate-180" />
                  </summary>
                  <p className="mt-2 whitespace-pre-wrap rounded-md bg-white p-3 text-[9px] leading-4 text-slate-600">
                    {scanResult.ai_report}
                  </p>
                </details>
              )}

              {!scanResult.ai_report && (
                <p className="mt-2 text-[8px] text-blue-500">
                  No narrative report for this scan.
                </p>
              )}
            </div>
          )}

          {/* Overall Confidence */}
          <div className="mt-4 rounded-lg border border-slate-300 bg-slate-50 p-4">
            <div className="flex items-end justify-between">
              <div>
                <p className="text-[9px] font-medium text-slate-500">
                  Compliance Score
                </p>
                <p className="mt-1 text-[24px] font-bold text-slate-800">
                  {scanResult ? `${scanResult.compliance_score}%` : "--"}
                </p>
              </div>
              <ShieldCheck
                size={25}
                className={
                  scanResult
                    ? scanResult.status === "Passed"
                      ? "text-green-500"
                      : "text-red-400"
                    : "text-slate-300"
                }
              />
            </div>

            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-full rounded-full transition-all duration-1000 ${
                  scanResult && scanResult.status === "Passed"
                    ? "bg-green-500"
                    : "bg-red-400"
                }`}
                style={{
                  width: scanResult ? `${scanResult.compliance_score}%` : "0%",
                }}
              />
            </div>
          </div>

          {/* Violations */}
          {scanResult && scanResult.violations.length > 0 && (
            <div className="mt-4 space-y-2 rounded-lg border border-red-100 bg-red-50/50 p-3">
              <p className="text-[9px] font-bold text-red-600">
                {scanResult.violations.length} Violation
                {scanResult.violations.length > 1 ? "s" : ""} Found
              </p>
              {scanResult.violations.map((v) => (
                <div key={v.id} className="rounded-md bg-white px-3 py-2 text-[9px]">
                  <p className="font-semibold text-slate-700">{v.label}</p>
                  <p className="mt-0.5 text-[8px] text-slate-400">
                    {v.rule_reference} • {v.severity.toUpperCase()}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="mt-4 grid grid-cols-2 gap-2">
            <button
              onClick={clearAllSides}
              disabled={scanning}
              className="flex h-10 items-center justify-center gap-2 rounded-md border border-slate-300 bg-white text-[9px] font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              <RefreshCw size={14} />
              NEW SCAN
            </button>

            <button
              disabled={!hasResult || downloadingReport}
              onClick={handleDownloadReport}
              className="flex h-10 items-center justify-center gap-2 rounded-md bg-[#07539a] text-[9px] font-semibold text-white hover:bg-[#06447f] disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Download size={14} />
              {downloadingReport ? "GENERATING..." : "DOWNLOAD REPORT"}
            </button>
          </div>

          {/* Status */}
          <div className="mt-4 rounded-md border border-blue-100 bg-blue-50 px-3 py-2.5">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
              <p className="text-[9px] font-semibold text-blue-700">
                {scanning
                  ? "Analyzing with OCR + AI model..."
                  : hasResult
                  ? "Scan complete"
                  : `Ready — ${sides.length} side${sides.length === 1 ? "" : "s"} waiting`}
              </p>
            </div>
            <p className="mt-1 text-[8px] text-blue-500">
              {hasResult
                ? `Inspected by ${scanResult.inspector_name || "you"} • saved to Scan History.`
                : "Capture each side, then press SCAN once for a combined result."}
            </p>
          </div>

        </section>
      </div>

      {/* ====================================================
          HIDDEN CANVAS
      ===================================================== */}

      <canvas ref={canvasRef} className="hidden" />

      {/* ====================================================
          PIPELINE
      ===================================================== */}

      <section className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="mb-3">
          <h3 className="text-[11px] font-bold text-slate-700">
            Inspection Pipeline
          </h3>
          <p className="text-[8px] text-slate-400">
            From multi-side capture to compliance verification
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Pipeline
            number="01"
            title="Capture Sides"
            description={`${sides.length} side${sides.length === 1 ? "" : "s"} added`}
            icon={Camera}
            active={sides.length > 0}
          />
          <Pipeline
            number="02"
            title="AI + OCR"
            description="Read every side at once"
            icon={ScanLine}
            active={scanning || hasResult}
          />
          <Pipeline
            number="03"
            title="Compliance"
            description="Validate declarations"
            icon={ShieldCheck}
            active={hasResult}
          />
          <Pipeline
            number="04"
            title="Report"
            description="Generate inspection report"
            icon={FileText}
            active={hasResult}
          />
        </div>
      </section>

    </div>
  );
}

/* ============================================================
   OCR FIELD
============================================================ */

function OCRField({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 px-3.5 py-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[8px] font-medium text-slate-500">{label}</p>
          <p className="mt-1 text-[14px] font-semibold text-slate-800">{value}</p>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   PIPELINE
============================================================ */

function Pipeline({ number, title, description, icon: Icon, active }) {
  return (
    <div
      className={`flex items-center gap-3 rounded-lg border p-3 ${
        active ? "border-blue-200 bg-blue-50/50" : "border-slate-200 bg-white"
      }`}
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${
          active ? "bg-[#07539a] text-white" : "bg-slate-100 text-slate-400"
        }`}
      >
        <Icon size={16} />
      </div>
      <div>
        <p className="text-[7px] font-bold text-slate-400">STEP {number}</p>
        <p className="text-[9px] font-bold text-slate-700">{title}</p>
        <p className="mt-0.5 text-[7px] text-slate-400">{description}</p>
      </div>
    </div>
  );
}
