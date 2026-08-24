import { Wallet, TrendingUp, TrendingDown } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

const CASH_DATA = [
  { day: "Mon", inflow: 4200, outflow: 3100 },
  { day: "Tue", inflow: 5800, outflow: 4200 },
  { day: "Wed", inflow: 3900, outflow: 3600 },
  { day: "Thu", inflow: 6700, outflow: 5100 },
  { day: "Fri", inflow: 5200, outflow: 4800 },
  { day: "Sat", inflow: 2100, outflow: 1800 },
  { day: "Sun", inflow: 1400, outflow: 1200 },
];

export function CashPosition() {
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Cash Position</h1>
          <p className="page-subtitle">Real-time inflow / outflow and liquidity overview</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { icon: Wallet,      label: "Net Position",  value: "$1.84M",  color: "text-[var(--navy)]" },
          { icon: TrendingUp,  label: "Total Inflow",  value: "+$29.3M", color: "text-emerald-500" },
          { icon: TrendingDown,label: "Total Outflow", value: "-$27.5M", color: "text-red-500" },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="kpi-card flex-row items-center">
            <Icon size={20} className={color} />
            <div>
              <p className={`text-xl font-bold font-mono ${color}`}>{value}</p>
              <p className="text-xs text-[var(--text-secondary)]">{label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-5">
          Weekly Cash Flow — Sample Data
        </h2>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={CASH_DATA} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="day" tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
            <Tooltip
              contentStyle={{
                background: "var(--bg-surface)", border: "1px solid var(--border)",
                borderRadius: 8, fontSize: 12, color: "var(--text-primary)",
              }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={((val: number, name: string) => [`$${val.toLocaleString()}`, name === "inflow" ? "Inflow" : "Outflow"]) as any}
            />
            <Bar dataKey="inflow"  fill="#10B981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="outflow" fill="#EF4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
