import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/state/auth";

export function UserProfile() {
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const navigate = useNavigate();

  if (!user) return null;

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      clearAuth();
      navigate("/login", { replace: true });
    }
  };

  const initial = user.name ? user.name.charAt(0).toUpperCase() : "U";

  return (
    <div className="flex items-center gap-2 pl-2 border-l border-gray-300">
      <div className="flex items-center gap-2">
        <div
          className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm"
          style={{ background: "var(--brand-mark)" }}
          title={`${user.name} • ${user.job_title || user.role_label} (${user.upn || user.email})${user.group_name ? ` • Group: ${user.group_name}` : ""}`}
        >
          {initial}
        </div>
        <div className="hidden 2xl:flex flex-col text-left">
          <span className="text-xs font-semibold leading-tight text-gray-900">{user.name}</span>
          <span
            className="text-[10px] leading-tight text-gray-500 truncate max-w-36"
            title={user.group_name || user.role_label}
          >
            {user.role_label}
          </span>
        </div>
      </div>
      <button
        type="button"
        onClick={handleLogout}
        className="btn text-xs py-1 px-2.5 font-medium hover:bg-red-50 hover:text-red-600 transition"
        title="Sign out of GTM Dashboard"
      >
        Sign Out
      </button>
    </div>
  );
}
