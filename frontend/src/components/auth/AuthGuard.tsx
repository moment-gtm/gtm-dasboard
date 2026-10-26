import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/state/auth";

export function AuthGuard() {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
