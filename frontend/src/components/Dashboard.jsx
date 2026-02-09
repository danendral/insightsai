/**
 * Dashboard Component
 *
 * KEY CONCEPT - useEffect for Data Fetching:
 * useEffect runs side effects (API calls, subscriptions) after the component renders.
 * The dependency array [] means "run once when the component mounts."
 * When [summary] changes, we re-fetch chart data.
 *
 * KEY CONCEPT - Component Composition:
 * Dashboard is built from smaller pieces: StatCard + chart sections.
 * Each chart section fetches its own data independently.
 */

import { useState, useEffect } from "react";
import {
  DollarSign,
  Users,
  TrendingUp,
  Target,
} from "lucide-react";
import { getChartData } from "@/lib/api";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#6366f1", "#06b6d4", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];

function StatCard({ icon: Icon, label, value, subtext }) {
  return (
    <div className="bg-surface rounded-xl border border-border p-5">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-sm text-text-muted">{label}</p>
          <p className="text-2xl font-bold text-text">{value}</p>
          {subtext && <p className="text-xs text-text-muted mt-0.5">{subtext}</p>}
        </div>
      </div>
    </div>
  );
}

function ChartCard({ title, children, className = "" }) {
  return (
    <div className={`bg-surface rounded-xl border border-border p-5 ${className}`}>
      <h3 className="text-sm font-semibold text-text mb-4">{title}</h3>
      {children}
    </div>
  );
}

export default function Dashboard({ summary }) {
  const [charts, setCharts] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch all chart data in parallel
    async function fetchCharts() {
      setLoading(true);
      try {
        const types = [
          "revenue-trend",
          "by-category",
          "by-region",
          "campaign-performance",
          "marketing-roi",
        ];
        const results = await Promise.all(
          types.map((t) => getChartData(t).then((r) => [t, r.data]))
        );
        setCharts(Object.fromEntries(results));
      } catch {
        // Charts will just be empty
      } finally {
        setLoading(false);
      }
    }
    fetchCharts();
  }, [summary]);

  // Compute top-level stats from summary
  const stats = summary.summary_stats || {};
  const totalRevenue = stats.revenue?.sum;
  const totalCustomers = stats.customers?.sum;
  const avgConversion = stats.conversion_rate?.mean;
  const totalLeads = stats.leads_generated?.sum;

  const fmt = (n) => {
    if (n == null) return "N/A";
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
    return `$${n}`;
  };

  const fmtNum = (n) => {
    if (n == null) return "N/A";
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={DollarSign}
          label="Total Revenue"
          value={fmt(totalRevenue)}
          subtext={`${summary.row_count} records`}
        />
        <StatCard
          icon={Users}
          label="Total Customers"
          value={fmtNum(totalCustomers)}
        />
        <StatCard
          icon={TrendingUp}
          label="Avg Conversion Rate"
          value={avgConversion != null ? `${avgConversion}%` : "N/A"}
        />
        <StatCard
          icon={Target}
          label="Total Leads"
          value={fmtNum(totalLeads)}
        />
      </div>

      {loading ? (
        <div className="text-center py-12 text-text-muted">
          Loading charts...
        </div>
      ) : (
        <>
          {/* Row 1: Revenue Trend (wide) */}
          {charts["revenue-trend"]?.length > 0 && (
            <ChartCard title="Revenue Trend">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={charts["revenue-trend"]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(v) => v.slice(5)}
                  />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
                  <Tooltip
                    formatter={(v) => [`$${v.toLocaleString()}`, ""]}
                    labelFormatter={(l) => `Month: ${l}`}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    stroke="#6366f1"
                    fill="#6366f1"
                    fillOpacity={0.1}
                    name="Revenue"
                  />
                  <Area
                    type="monotone"
                    dataKey="customers"
                    stroke="#06b6d4"
                    fill="#06b6d4"
                    fillOpacity={0.1}
                    yAxisId={0}
                    name="Customers"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {/* Row 2: Category + Region */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {charts["by-category"]?.length > 0 && (
              <ChartCard title="Revenue by Product Category">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={charts["by-category"]}
                      dataKey="revenue"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={({ category, percent }) =>
                        `${category} ${(percent * 100).toFixed(0)}%`
                      }
                    >
                      {charts["by-category"].map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            )}

            {charts["by-region"]?.length > 0 && (
              <ChartCard title="Revenue by Region">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={charts["by-region"]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="region" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
                    <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
                    <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            )}
          </div>

          {/* Row 3: Campaign Performance */}
          {charts["campaign-performance"]?.length > 0 && (
            <ChartCard title="Campaign Performance: Revenue vs Marketing Spend">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={charts["campaign-performance"]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="campaign" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
                  <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
                  <Legend />
                  <Bar dataKey="revenue" fill="#6366f1" name="Revenue" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="marketing_spend" fill="#f59e0b" name="Marketing Spend" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {/* Row 4: Marketing ROI */}
          {charts["marketing-roi"]?.length > 0 && (
            <ChartCard title="Marketing ROI Over Time">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={charts["marketing-roi"]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(v) => v.slice(5)}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(v, name) =>
                      name === "ROI" ? [`${v}x`, name] : [`$${v.toLocaleString()}`, name]
                    }
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="roi"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="ROI"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </>
      )}
    </div>
  );
}
