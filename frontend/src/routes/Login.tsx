import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/state/auth";

export function Login() {
  const [upn, setUpn] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);

  const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || "/executive";

  const handleEntraLogin = async (targetUpn: string, targetPass?: string) => {
    if (!targetUpn.trim()) {
      setError("Please provide a valid Microsoft Entra User Principal Name (UPN).");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const cleanPass = targetPass?.trim() ? targetPass.trim() : undefined;
      const res = await authApi.loginWithEntra(targetUpn.trim(), cleanPass);
      setAuth(res.access_token, res.user);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || "Entra ID authentication failed. Verify corporate account.");
      } else {
        setError("An unexpected authentication error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void handleEntraLogin(upn, password);
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center p-4 md:p-8"
      style={{
        background: "radial-gradient(ellipse at 50% 15%, #184f95 0%, #0d1b33 60%, #070e1c 100%)",
      }}
    >
      <div className="w-full max-w-lg">
        {/* Main Card */}
        <div
          className="rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-sm"
          style={{
            background: "rgba(252, 252, 251, 0.98)",
            border: "1px solid rgba(255, 255, 255, 0.25)",
            boxShadow: "0 24px 48px rgba(0, 0, 0, 0.4)",
          }}
        >
          {/* Header with Microsoft & Moment Branding */}
          <div className="mb-6 flex flex-col items-center text-center">
            <div className="flex items-center gap-3 mb-2">
              {/* Microsoft Entra Logo */}
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-sm border border-gray-200">
                <svg className="w-5 h-5" viewBox="0 0 21 21" fill="none">
                  <rect x="1" y="1" width="9" height="9" fill="#f25022" />
                  <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
                  <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
                  <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
                </svg>
              </div>
              <span className="text-sm font-semibold tracking-wide text-gray-500 uppercase">
                Microsoft Entra ID
              </span>
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-gray-900 md:text-3xl">
              Moment GTM Dashboard
            </h1>
            <p className="mt-1 text-sm text-gray-600 max-w-sm">
              Executive Go-to-Market Analytics & Intelligence • Synthetic Demo Portal
            </p>

            <div
              className="mt-2.5 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium"
              style={{
                background: "var(--accent-wash, #e8f1fc)",
                color: "var(--accent-strong, #184f95)",
              }}
            >
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Frontend mock data mode — no backend required</span>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <div
              className="mb-5 flex items-start gap-3 rounded-lg p-3.5 text-sm"
              style={{
                background: "var(--status-off-track-bg, #fbe9e9)",
                border: "1px solid #d03b3b",
                color: "#a12626",
              }}
              role="alert"
            >
              <svg className="h-5 w-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="font-medium">{error}</span>
            </div>
          )}

          {/* Section: Sign In with Corporate Work Account (UPN) */}
          <div className="mb-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-gray-800">
              Sign In with Corporate Work Account (UPN)
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Choose a synthetic demo persona. Data is bundled with the frontend and saved settings
              stay in this browser.
            </p>
          </div>

          {/* Corporate UPN Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="upn"
                className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1"
              >
                Corporate UPN / Work Email
              </label>
              <input
                id="upn"
                type="text"
                autoComplete="username"
                required
                value={upn}
                onChange={(e) => setUpn(e.target.value)}
                placeholder="e.g. jordan.avery@moment.example"
                className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 focus:border-blue-600 focus:ring-1 focus:ring-blue-600 focus:outline-none"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold uppercase tracking-wider text-gray-700"
                >
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-xs font-medium text-blue-600 hover:text-blue-800"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Moment#2026$FirstName!GTM"
                className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 focus:border-blue-600 focus:ring-1 focus:ring-blue-600 focus:outline-none"
              />
              <p className="mt-1 text-xs text-gray-500">
                Synthetic demo password format: Moment#2026$FirstName!GTM
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg py-2.5 px-4 font-semibold text-white shadow-md transition hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 flex items-center justify-center gap-2 pt-2.5"
              style={{ background: "var(--brand-mark)" }}
            >
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 21 21" fill="none">
                <rect x="1" y="1" width="9" height="9" fill="#f25022" />
                <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
                <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
                <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
              </svg>
              <span>
                {loading
                  ? "Authenticating with Microsoft Entra ID..."
                  : "Sign in with Microsoft Entra ID"}
              </span>
            </button>
          </form>

          {/* Footer Architecture Note */}
          <div className="mt-5 pt-3 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between text-[11px] text-gray-500 gap-2">
            <span>Synthetic persona simulation only — not corporate SSO or production RLS</span>
            <span>
              Switch to Azure AD Production via{" "}
              <code className="bg-gray-100 px-1 py-0.5 rounded text-gray-700">
                GTM_AUTH_MODE=entra
              </code>
            </span>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-3 text-center text-xs text-blue-200/80">
          Synthetic demo data only. Do not use for real customer data or access-control testing.
        </div>
      </div>
    </div>
  );
}
