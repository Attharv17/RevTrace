import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  RefreshCcw,
  AlertTriangle,
  Landmark,
  Wallet,
  Bot,
  ClipboardList,
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
  { id: "overview",       label: "Overview",       path: "/",              icon: LayoutDashboard },
  { id: "reconciliation", label: "Reconciliation", path: "/reconciliation", icon: RefreshCcw },
  { id: "exceptions",     label: "Exceptions",     path: "/exceptions",    icon: AlertTriangle,  badge: 3 },
  { id: "settlements",    label: "Settlements",    path: "/settlements",   icon: Landmark },
  { id: "cash-position",  label: "Cash Position",  path: "/cash-position", icon: Wallet },
  { id: "ai-assistant",   label: "AI Assistant",   path: "/ai-assistant",  icon: Bot },
  { id: "audit-trail",    label: "Audit Trail",    path: "/audit-trail",   icon: ClipboardList },
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
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-navy-500 dark:bg-navy-600 flex items-center justify-center">
          <Zap size={16} className="text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <p className="text-sm font-bold text-[var(--text-primary)] tracking-tight leading-none">
              LedgerPilot
            </p>
            <p className="text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-widest mt-0.5">
              Finance Control
            </p>
          </div>
        )}
      </div>

      {/* ── Navigation ───────────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
        {NAV_ITEMS.map(({ id, label, path, icon: Icon, badge }) => {
          const isActive =
            path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);

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
              {badge && !collapsed && (
                <span className="ml-auto flex-shrink-0 bg-accent-red text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center">
                  {badge}
                </span>
              )}
              {badge && collapsed && (
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-accent-red" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* ── Collapse Toggle ───────────────────────────────────────────── */}
      <div className="p-2 border-t border-[var(--border)]">
        <button
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
