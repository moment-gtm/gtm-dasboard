import * as Tooltip from "@radix-ui/react-tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ApiError } from "@/api/client";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { AppShell } from "@/components/layout/AppShell";
import { MODULES } from "@/components/layout/modules";
import { Accounts } from "@/routes/Accounts";
import { Admin } from "@/routes/Admin";
import { ComingSoon } from "@/routes/ComingSoon";
import { Executive } from "@/routes/Executive";
import { Login } from "@/routes/Login";
import { MarketSignals } from "@/routes/MarketSignals";
import { Offerings } from "@/routes/Offerings";
import { Partners } from "@/routes/Partners";
import { Pipeline } from "@/routes/Pipeline";
import { Pursuits } from "@/routes/Pursuits";
import { SolutionsCapacity } from "@/routes/SolutionsCapacity";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // Don't retry auth/validation errors; retry transient failures once.
      retry: (count, err) =>
        !(err instanceof ApiError && err.status >= 400 && err.status < 500) && count < 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Tooltip.Provider delayDuration={200}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<AuthGuard />}>
              <Route element={<AppShell />}>
                <Route index element={<Navigate to="/executive" replace />} />
                <Route path="/executive" element={<Executive />} />
                <Route path="/pipeline" element={<Pipeline />} />
                <Route path="/pursuits" element={<Pursuits />} />
                <Route path="/offerings" element={<Offerings />} />
                <Route path="/accounts" element={<Accounts />} />
                <Route path="/partners" element={<Partners />} />
                <Route path="/solutions-capacity" element={<SolutionsCapacity />} />
                <Route path="/market-signals" element={<MarketSignals />} />
                <Route path="/admin" element={<Admin />} />
                {MODULES.filter((m) => !m.built).map((m) => (
                  <Route key={m.key} path={m.path} element={<ComingSoon moduleKey={m.key} />} />
                ))}
                <Route path="*" element={<Navigate to="/executive" replace />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </Tooltip.Provider>
    </QueryClientProvider>
  );
}
