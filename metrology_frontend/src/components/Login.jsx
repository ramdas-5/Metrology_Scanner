import  { useState } from "react";
import { Lock, Mail, ScanLine, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    setSubmitting(true);
    const ok = await login(email, password);
    setSubmitting(false);
    if (!ok) {
      setLocalError("Invalid email or password. Please try again.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f8fc] p-5">
      <div className="w-full max-w-[380px] rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-[#07539a] text-white">
            <ScanLine size={24} />
          </div>
          <h1 className="text-[16px] font-bold text-slate-800">METROLOGY SCANNER</h1>
          <p className="mt-1 text-[10px] text-slate-400">
            Legal Metrology Compliance Platform
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block text-[9px] font-semibold text-slate-500">
              Email Address
            </label>
            <div className="flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2.5">
              <Mail size={14} className="text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@department.gov.in"
                className="w-full text-[11px] outline-none placeholder:text-slate-300"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-[9px] font-semibold text-slate-500">
              Password
            </label>
            <div className="flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2.5">
              <Lock size={14} className="text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full text-[11px] outline-none placeholder:text-slate-300"
              />
            </div>
          </div>

          {(localError || error) && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-[9px] font-medium text-red-600">
              {localError || error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 flex h-10 w-full items-center justify-center gap-2 rounded-md bg-[#07539a] text-[11px] font-bold text-white transition hover:bg-[#0866b7] disabled:opacity-50"
          >
            <ShieldCheck size={15} />
            {submitting ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="mt-5 text-center text-[8px] text-slate-400">
          Accounts are created by your system administrator via the Admin
          Panel, or with the backend's <code>seed_admin.py</code> script.
        </p>
      </div>
    </div>
  );
}
