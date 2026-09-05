import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { cn } from "@/lib/utils";

// Map route paths → readable page titles
const PAGE_TITLES: Record<string, string> = {
  "/overview":      "Overview",
  "/recovery":      "Recovery",
  "/opportunities": "Opportunities",
  "/transactions":  "Transactions",
  "/analytics":     "Analytics",
  "/assistant":     "AI Assistant",
  "/simulator":     "Simulator",
  "/audit":         "Audit Log",
  "/evaluation":    "Evaluation",
};

export function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();
  const pageTitle = PAGE_TITLES[location.pathname] ?? "RevTrace";

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
      />

      {/* Topbar + main content — offset by sidebar width */}
      <div
        className={cn(
          "flex flex-col min-h-screen transition-[margin-left] duration-200"
        )}
        style={{ marginLeft: sidebarCollapsed ? 72 : 256 }}
      >
        <Topbar sidebarCollapsed={sidebarCollapsed} pageTitle={pageTitle} />

        {/* Page content */}
        <main className="flex-1 mt-16 p-6 animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
