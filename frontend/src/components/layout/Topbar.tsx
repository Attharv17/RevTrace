import { useEffect, useState } from "react";
import { Sun, Moon, Bell, Search, User, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/hooks/useTheme";
import { api } from "@/api/client";
import type { HealthResponse } from "@/types";

interface TopbarProps {
  sidebarCollapsed: boolean;
  pageTitle?: string;
}

export function Topbar({ sidebarCollapsed, pageTitle }: TopbarProps) {
  const { toggle, isDark } = useTheme();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  // Poll health every 30 s
  useEffect(() => {
    const check = () =>
      api
        .get<HealthResponse>("/api/health")
        .then(setHealth)
        .catch(() => setHealth(null));

    check();
    const id = setInterval(check, 30_000);
    return () => clearInterval(id);
  }, []);

  const sidebarWidth = sidebarCollapsed ? 72 : 256;

  return (
    <header
      className={cn(
        "fixed top-0 right-0 z-20 h-16 flex items-center",
        "bg-[var(--bg-surface)] border-b border-[var(--border)]",
        "px-6 transition-[left] duration-200"
      )}
      style={{ left: sidebarWidth }}
    >
      {/* Page title */}
      <div className="flex-1">
        {pageTitle && (
          <h1 className="text-base font-semibold text-[var(--text-primary)]">
            {pageTitle}
          </h1>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        {/* API status pill */}
        {health && (
          <div
            className={cn(
              "hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border",
              health.status === "ok"
                ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400"
                : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400"
            )}
          >
            <Activity size={11} />
            API {health.status === "ok" ? "Online" : "Degraded"}
          </div>
        )}

        {/* Search */}
        <button
          id="topbar-search-btn"
          className="btn-ghost p-2"
          title="Search"
        >
          <Search size={17} />
        </button>

        {/* Notifications */}
        <button
          id="topbar-notifications-btn"
          className="btn-ghost p-2 relative"
          title="Notifications"
        >
          <Bell size={17} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-accent-red" />
        </button>

        {/* Theme toggle */}
        <button
          id="topbar-theme-toggle"
          onClick={toggle}
          className="btn-ghost p-2"
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {isDark ? <Sun size={17} /> : <Moon size={17} />}
        </button>

        {/* Avatar */}
        <button
          id="topbar-user-btn"
          className={cn(
            "ml-1 w-8 h-8 rounded-full flex items-center justify-center",
            "bg-navy-500 dark:bg-navy-600 text-white",
            "hover:opacity-90 transition-opacity"
          )}
          title="Account"
        >
          <User size={15} />
        </button>
      </div>
    </header>
  );
}
