import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  RefreshCcw,
  Target,
  CreditCard,
  BarChart2,
  Bot,
  FlaskConical,
  ClipboardList,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const NAV_ITEMS = [
  { id: "overview",      label: "Overview",      path: "/overview",      icon: LayoutDashboard },
  { id: "recovery",      label: "Recovery",       path: "/recovery",      icon: RefreshCcw },
  { id: "opportunities", label: "Opportunities",  path: "/opportunities", icon: Target },
  { id: "transactions",  label: "Transactions",   path: "/transactions",  icon: CreditCard },
  { id: "analytics",     label: "Analytics",      path: "/analytics",     icon: BarChart2 },
  { id: "assistant",     label: "AI Assistant",   path: "/assistant",     icon: Bot },
  { id: "simulator",     label: "Simulator",      path: "/simulator",     icon: FlaskConical },
  { id: "audit",         label: "Audit Log",      path: "/audit",         icon: ClipboardList },
  { id: "evaluation",    label: "Evaluation",     path: "/evaluation",    icon: CheckSquare },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-full z-30 flex flex-col",
        "bg-[var(--bg-surface)] border-r border-[var(--border)]",
        "transition-[width] duration-200 ease-in-out",
        collapsed ? "w-[72px]" : "w-[256px]"
      )}
    >
      {/* ── Logo ─────────────────────────────────────────────────────── */}
      <div
        className={cn(
          "flex items-center h-16 px-4 border-b border-[var(--border)]",
          collapsed ? "justify-center" : "gap-3"
        )}
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-[#7C3AED] flex items-center justify-center shadow-sm">
          <Zap size={16} className="text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <p className="text-sm font-bold text-[var(--text-primary)] tracking-tight leading-none">
              RevTrace
            </p>
            <p className="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-widest mt-0.5">
              Revenue Recovery
            </p>
          </div>
        )}
      </div>

      {/* ── Navigation ───────────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
        {NAV_ITEMS.map(({ id, label, path, icon: Icon }) => {
          const isActive = location.pathname === path;

          return (
            <NavLink
              key={id}
              to={path}
              className={cn(
                "nav-item group relative",
                isActive && "active",
                collapsed && "justify-center px-0"
              )}
              title={collapsed ? label : undefined}
            >
              <Icon
                size={18}
                className={cn(
                  "flex-shrink-0 transition-colors",
                  isActive
                    ? "text-[var(--navy)]"
                    : "text-[var(--text-secondary)] group-hover:text-[var(--navy)]"
                )}
              />
              {!collapsed && (
                <span className="flex-1 truncate animate-fade-in">{label}</span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* ── Collapse Toggle ───────────────────────────────────────────── */}
      <div className="p-2 border-t border-[var(--border)]">
        <button
          id="sidebar-collapse-btn"
          onClick={onToggle}
          className={cn(
            "w-full flex items-center justify-center p-2 rounded-lg",
            "text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
            "hover:bg-[var(--bg-surface-3)] transition-colors duration-150"
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          {!collapsed && (
            <span className="ml-2 text-xs animate-fade-in">Collapse</span>
          )}
        </button>
      </div>
    </aside>
  );
}
