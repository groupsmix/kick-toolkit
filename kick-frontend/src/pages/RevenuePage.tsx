import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
} from "recharts";
import {
  DollarSign,
  TrendingUp,
  Download,
  PlusCircle,
  CreditCard,
  Gift,
  Handshake,
  ShoppingBag,
  MoreHorizontal,
  ArrowUpRight,
  ArrowDownRight,
  Receipt,
  BarChart3,
} from "lucide-react";

interface RevenueEntry {
  id: string;
  channel: string;
  source: string;
  amount: number;
  currency: string;
  description: string;
  stream_session_id: string | null;
  date: string;
  created_at: string;
}

interface RevenueSummary {
  channel: string;
  total_revenue: number;
  total_this_month: number;
  total_last_month: number;
  month_over_month_change: number;
  by_source: { source: string; total: number }[];
  monthly_totals: { month: string; total: number }[];
  per_stream: { session_id: string; revenue: number; date: string }[];
  forecast_next_month: number;
}

const SOURCE_CONFIG: Record<string, { icon: typeof CreditCard; color: string; bg: string; label: string }> = {
  subscription: { icon: CreditCard, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Subscriptions" },
  tip: { icon: Gift, color: "text-amber-400", bg: "bg-amber-500/10", label: "Tips" },
  sponsor: { icon: Handshake, color: "text-blue-400", bg: "bg-blue-500/10", label: "Sponsors" },
  merch: { icon: ShoppingBag, color: "text-violet-400", bg: "bg-violet-500/10", label: "Merch" },
  other: { icon: MoreHorizontal, color: "text-zinc-400", bg: "bg-zinc-500/10", label: "Other" },
};

const PIE_COLORS = ["#10b981", "#f59e0b", "#3b82f6", "#8b5cf6", "#71717a"];

export function RevenuePage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";

  const [summary, setSummary] = useState<RevenueSummary | null>(null);
  const [entries, setEntries] = useState<RevenueEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [newEntry, setNewEntry] = useState({
    source: "tip",
    amount: 0,
    description: "",
    date: new Date().toISOString().split("T")[0],
  });

  const fetchData = useCallback(async () => {
    try {
      const [summaryData, entriesData] = await Promise.all([
        api<RevenueSummary>(`/api/revenue/summary/${channel}`),
        api<RevenueEntry[]>(`/api/revenue/entries/${channel}?limit=50`),
      ]);
      setSummary(summaryData);
      setEntries(entriesData);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load revenue data");
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => {
    if (channel) fetchData();
  }, [channel, fetchData]);

  const addEntry = async () => {
    try {
      await api(`/api/revenue/entries/${channel}`, {
        method: "POST",
        body: JSON.stringify(newEntry),
      });
      toast.success("Revenue entry added!");
      setNewEntry({ source: "tip", amount: 0, description: "", date: new Date().toISOString().split("T")[0] });
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add entry");
    }
  };

  const deleteEntry = async (id: string) => {
    try {
      await api(`/api/revenue/entries/${id}`, { method: "DELETE" });
      toast.success("Entry deleted");
      fetchData();
    } catch {
      toast.error("Failed to delete entry");
    }
  };

  const exportCSV = () => {
    window.open(
      `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/revenue/export/${channel}`,
      "_blank"
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const monthlyChart = summary?.monthly_totals.map((m) => ({
    month: m.month,
    total: m.total,
  })) || [];

  const pieData = summary?.by_source.map((s) => ({
    name: SOURCE_CONFIG[s.source]?.label || s.source,
    value: s.total,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-emerald-500/20 via-amber-500/10 to-transparent border border-emerald-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-6 h-6 text-emerald-400" />
              <h2 className="text-2xl font-bold text-white">Revenue Intelligence</h2>
              <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px] uppercase font-bold">
                Business
              </Badge>
            </div>
            <p className="text-zinc-400">
              Track all income sources. Subscriptions, tips, sponsors, merch — all in one view.
            </p>
          </div>
          <Button variant="outline" className="border-zinc-700" onClick={exportCSV}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <DollarSign className="w-32 h-32 text-emerald-500" />
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <DollarSign className="w-5 h-5 text-emerald-400 mb-2" />
              <p className="text-2xl font-bold text-white">${summary.total_revenue.toLocaleString()}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Total Revenue</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <Receipt className="w-5 h-5 text-blue-400 mb-2" />
              <p className="text-2xl font-bold text-white">${summary.total_this_month.toLocaleString()}</p>
              <p className="text-[10px] text-zinc-500 uppercase">This Month</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <div className="flex items-center gap-1 mb-2">
                {summary.month_over_month_change >= 0 ? (
                  <ArrowUpRight className="w-5 h-5 text-emerald-400" />
                ) : (
                  <ArrowDownRight className="w-5 h-5 text-red-400" />
                )}
              </div>
              <p className={`text-2xl font-bold ${summary.month_over_month_change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {summary.month_over_month_change >= 0 ? "+" : ""}{summary.month_over_month_change}%
              </p>
              <p className="text-[10px] text-zinc-500 uppercase">MoM Change</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-4">
              <TrendingUp className="w-5 h-5 text-amber-400 mb-2" />
              <p className="text-2xl font-bold text-white">${summary.forecast_next_month.toLocaleString()}</p>
              <p className="text-[10px] text-zinc-500 uppercase">Forecast</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="overview" className="data-[state=active]:bg-zinc-800">
            Overview
          </TabsTrigger>
          <TabsTrigger value="entries" className="data-[state=active]:bg-zinc-800">
            Entries
          </TabsTrigger>
          <TabsTrigger value="add" className="data-[state=active]:bg-zinc-800">
            Add Entry
          </TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Monthly Revenue */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  Monthly Revenue
                </CardTitle>
              </CardHeader>
              <CardContent>
                {monthlyChart.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={monthlyChart}>
                      <defs>
                        <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="month" tick={{ fill: "#71717a", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#71717a", fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                      <Tooltip
                        contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                        formatter={(value: number) => [`$${value.toFixed(2)}`, "Revenue"]}
                      />
                      <Area type="monotone" dataKey="total" stroke="#10b981" fill="url(#revenueGrad)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-zinc-600 text-sm">
                    No monthly data yet
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Revenue by Source */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-amber-400" />
                  Revenue by Source
                </CardTitle>
              </CardHeader>
              <CardContent>
                {pieData.length > 0 ? (
                  <div className="flex items-center gap-4">
                    <ResponsiveContainer width="50%" height={200}>
                      <PieChart>
                        <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={80} innerRadius={40}>
                          {pieData.map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                          formatter={(value: number) => [`$${value.toFixed(2)}`, ""]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-2">
                      {summary?.by_source.map((s, i) => {
                        const cfg = SOURCE_CONFIG[s.source] || SOURCE_CONFIG.other;
                        const Icon = cfg.icon;
                        return (
                          <div key={s.source} className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                            <Icon className={`w-3 h-3 ${cfg.color}`} />
                            <span className="text-xs text-zinc-400">{cfg.label}</span>
                            <span className="text-xs text-white font-medium">${s.total.toFixed(2)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="h-[200px] flex items-center justify-center text-zinc-600 text-sm">
                    No source data yet
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Revenue per Stream */}
          {summary?.per_stream && summary.per_stream.length > 0 && (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-400" />
                  Revenue per Stream
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={summary.per_stream}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 11 }} />
                    <YAxis tick={{ fill: "#71717a", fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                    <Tooltip
                      contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8 }}
                      formatter={(value: number) => [`$${value.toFixed(2)}`, "Revenue"]}
                    />
                    <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Entries */}
        <TabsContent value="entries" className="space-y-2">
          {entries.map((e) => {
            const cfg = SOURCE_CONFIG[e.source] || SOURCE_CONFIG.other;
            const Icon = cfg.icon;
            return (
              <Card key={e.id} className="bg-zinc-900/30 border-zinc-800/50">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full ${cfg.bg} flex items-center justify-center`}>
                      <Icon className={`w-4 h-4 ${cfg.color}`} />
                    </div>
                    <div>
                      <p className="text-sm text-white">{e.description || cfg.label}</p>
                      <p className="text-[10px] text-zinc-500">{e.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-emerald-400">
                      +${e.amount.toFixed(2)}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-zinc-600 hover:text-red-400 text-xs"
                      onClick={() => deleteEntry(e.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
          {entries.length === 0 && (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center">
                <DollarSign className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No revenue entries yet</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Add Entry */}
        <TabsContent value="add" className="space-y-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-emerald-400" />
                Add Revenue Entry
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <Label className="text-xs text-zinc-500">Source</Label>
                  <select
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-md text-white text-sm p-2 mt-1"
                    value={newEntry.source}
                    onChange={(e) => setNewEntry({ ...newEntry, source: e.target.value })}
                  >
                    <option value="subscription">Subscription</option>
                    <option value="tip">Tip</option>
                    <option value="sponsor">Sponsor</option>
                    <option value="merch">Merch</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Amount ($)</Label>
                  <Input
                    type="number"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={newEntry.amount}
                    onChange={(e) => setNewEntry({ ...newEntry, amount: +e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Date</Label>
                  <Input
                    type="date"
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={newEntry.date}
                    onChange={(e) => setNewEntry({ ...newEntry, date: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Description</Label>
                  <Input
                    className="bg-zinc-800 border-zinc-700 mt-1"
                    value={newEntry.description}
                    onChange={(e) => setNewEntry({ ...newEntry, description: e.target.value })}
                    placeholder="e.g. 5 gifted subs"
                  />
                </div>
              </div>
              <Button
                className="mt-4 bg-emerald-600 hover:bg-emerald-700"
                onClick={addEntry}
              >
                <PlusCircle className="w-4 h-4 mr-2" />
                Add Entry
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
