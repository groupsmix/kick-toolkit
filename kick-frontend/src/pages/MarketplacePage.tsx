import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  Store,
  Star,
  Download,
  Search,
  Plus,
  Trash2,
  DollarSign,
  TrendingUp,
  Package,
  ShoppingCart,
  Eye,
  BarChart3,
  User,
  Tag,
  Palette,
  Bell,
  Puzzle,
  Bot,
  Pencil,
} from "lucide-react";
import type {
  MarketplaceItem,
  SellerProfile,
  MarketplacePurchase,
  MarketplaceReview,
  SellerRevenueAnalytics,
} from "@/types";

const CATEGORIES = [
  { value: "overlay", label: "Overlays", icon: Palette },
  { value: "alert_pack", label: "Alert Packs", icon: Bell },
  { value: "widget_skin", label: "Widget Skins", icon: Puzzle },
  { value: "chatbot_preset", label: "Chatbot Presets", icon: Bot },
];

const SORT_OPTIONS = [
  { value: "newest", label: "Newest" },
  { value: "popular", label: "Most Popular" },
  { value: "rating", label: "Top Rated" },
  { value: "price_low", label: "Price: Low to High" },
  { value: "price_high", label: "Price: High to Low" },
];

function StarRating({ rating, count }: { rating: number; count?: number }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star
          key={s}
          className={`w-3.5 h-3.5 ${
            s <= Math.round(rating)
              ? "text-amber-400 fill-amber-400"
              : "text-zinc-600"
          }`}
        />
      ))}
      {count !== undefined && (
        <span className="text-xs text-zinc-500 ml-1">({count})</span>
      )}
    </div>
  );
}

function CategoryBadge({ category }: { category: string }) {
  const cat = CATEGORIES.find((c) => c.value === category);
  const colorMap: Record<string, string> = {
    overlay: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    alert_pack: "bg-rose-500/20 text-rose-400 border-rose-500/30",
    widget_skin: "bg-sky-500/20 text-sky-400 border-sky-500/30",
    chatbot_preset: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  };
  return (
    <Badge className={`text-[10px] ${colorMap[category] || "bg-zinc-500/20 text-zinc-400"}`}>
      {cat?.label || category}
    </Badge>
  );
}

export function MarketplacePage() {
  useAuth();

  const [activeTab, setActiveTab] = useState("browse");
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [sortBy, setSortBy] = useState("newest");
  const [selectedItem, setSelectedItem] = useState<MarketplaceItem | null>(null);
  const [itemReviews, setItemReviews] = useState<MarketplaceReview[]>([]);

  // Seller state
  const [sellerProfile, setSellerProfile] = useState<SellerProfile | null>(null);
  const [sellerItems, setSellerItems] = useState<MarketplaceItem[]>([]);
  const [revenue, setRevenue] = useState<SellerRevenueAnalytics | null>(null);
  const [purchases, setPurchases] = useState<MarketplacePurchase[]>([]);
  const [showCreateItem, setShowCreateItem] = useState(false);
  const [showSetupSeller, setShowSetupSeller] = useState(false);
  const [showReviewDialog, setShowReviewDialog] = useState(false);

  const [itemForm, setItemForm] = useState({
    title: "",
    description: "",
    category: "overlay",
    price: "",
    preview_url: "",
    download_url: "",
    thumbnail_url: "",
    tags: "",
  });

  const [sellerForm, setSellerForm] = useState({
    display_name: "",
    bio: "",
    website: "",
  });

  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: "" });

  // Fetch store items
  const fetchItems = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCategory && selectedCategory !== "all") params.set("category", selectedCategory);
      if (searchQuery) params.set("search", searchQuery);
      if (sortBy) params.set("sort", sortBy);
      const query = params.toString();
      const data = await api<MarketplaceItem[]>(`/api/marketplace/items${query ? `?${query}` : ""}`);
      setItems(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load items";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery, sortBy]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  // Fetch seller data when switching to seller tab
  useEffect(() => {
    if (activeTab === "seller" || activeTab === "revenue") {
      api<SellerProfile>("/api/marketplace/seller/profile")
        .then((p) => {
          setSellerProfile(p);
          api<MarketplaceItem[]>("/api/marketplace/seller/items").then(setSellerItems).catch(() => {});
          api<SellerRevenueAnalytics>("/api/marketplace/seller/revenue").then(setRevenue).catch(() => {});
        })
        .catch(() => setSellerProfile(null));
    }
  }, [activeTab]);

  // Fetch purchases when switching to purchases tab
  useEffect(() => {
    if (activeTab === "purchases") {
      api<MarketplacePurchase[]>("/api/marketplace/purchases")
        .then(setPurchases)
        .catch(() => setPurchases([]));
    }
  }, [activeTab]);

  const openItemDetail = async (item: MarketplaceItem) => {
    setSelectedItem(item);
    try {
      const reviews = await api<MarketplaceReview[]>(`/api/marketplace/items/${item.id}/reviews`);
      setItemReviews(reviews);
    } catch {
      setItemReviews([]);
    }
  };

  const purchaseItem = async (item: MarketplaceItem) => {
    try {
      await api<MarketplacePurchase>(`/api/marketplace/items/${item.id}/purchase`, {
        method: "POST",
      });
      toast.success(`Purchased "${item.title}"!`);
      setSelectedItem(null);
      fetchItems();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Purchase failed");
    }
  };

  const setupSeller = async () => {
    if (!sellerForm.display_name) {
      toast.error("Display name is required");
      return;
    }
    try {
      const profile = await api<SellerProfile>("/api/marketplace/seller/profile", {
        method: "POST",
        body: JSON.stringify({
          display_name: sellerForm.display_name,
          bio: sellerForm.bio,
          website: sellerForm.website || null,
        }),
      });
      setSellerProfile(profile);
      setShowSetupSeller(false);
      toast.success("Seller profile created!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create profile");
    }
  };

  const createItem = async () => {
    if (!itemForm.title) {
      toast.error("Title is required");
      return;
    }
    try {
      const item = await api<MarketplaceItem>("/api/marketplace/seller/items", {
        method: "POST",
        body: JSON.stringify({
          title: itemForm.title,
          description: itemForm.description,
          category: itemForm.category,
          price: parseFloat(itemForm.price) || 0,
          preview_url: itemForm.preview_url || null,
          download_url: itemForm.download_url || null,
          thumbnail_url: itemForm.thumbnail_url || null,
          tags: itemForm.tags ? itemForm.tags.split(",").map((t) => t.trim()) : [],
        }),
      });
      setSellerItems((prev) => [item, ...prev]);
      setShowCreateItem(false);
      setItemForm({
        title: "", description: "", category: "overlay", price: "",
        preview_url: "", download_url: "", thumbnail_url: "", tags: "",
      });
      toast.success("Item listed!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create item");
    }
  };

  const deleteSellerItem = async (itemId: string) => {
    try {
      await api(`/api/marketplace/seller/items/${itemId}`, { method: "DELETE" });
      setSellerItems((prev) => prev.filter((i) => i.id !== itemId));
      toast.success("Item deleted");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete item");
    }
  };

  const submitReview = async () => {
    if (!selectedItem) return;
    try {
      await api(`/api/marketplace/items/${selectedItem.id}/reviews`, {
        method: "POST",
        body: JSON.stringify({ rating: reviewForm.rating, comment: reviewForm.comment }),
      });
      toast.success("Review submitted!");
      setShowReviewDialog(false);
      setReviewForm({ rating: 5, comment: "" });
      // Refresh reviews
      const reviews = await api<MarketplaceReview[]>(`/api/marketplace/items/${selectedItem.id}/reviews`);
      setItemReviews(reviews);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to submit review");
    }
  };

  const formatPrice = (price: number) =>
    price === 0 ? "Free" : `$${price.toFixed(2)}`;

  const formatDate = (ts: string) =>
    new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-orange-500/20 via-amber-500/10 to-transparent border border-orange-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Store className="w-6 h-6 text-orange-400" />
              <h2 className="text-2xl font-bold text-white">Creator Marketplace</h2>
              <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/30 text-[10px] uppercase font-bold">
                New
              </Badge>
            </div>
            <p className="text-zinc-400">
              Buy and sell overlays, alert packs, widget skins, and chatbot presets. 20% platform fee on sales.
            </p>
          </div>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Store className="w-32 h-32 text-orange-500" />
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="browse" className="data-[state=active]:bg-zinc-800">
            <ShoppingCart className="w-4 h-4 mr-1" />
            Browse
          </TabsTrigger>
          <TabsTrigger value="purchases" className="data-[state=active]:bg-zinc-800">
            <Package className="w-4 h-4 mr-1" />
            My Purchases
          </TabsTrigger>
          <TabsTrigger value="seller" className="data-[state=active]:bg-zinc-800">
            <User className="w-4 h-4 mr-1" />
            Seller Dashboard
          </TabsTrigger>
          <TabsTrigger value="revenue" className="data-[state=active]:bg-zinc-800">
            <BarChart3 className="w-4 h-4 mr-1" />
            Revenue
          </TabsTrigger>
        </TabsList>

        {/* ===== Browse Tab ===== */}
        <TabsContent value="browse" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                placeholder="Search overlays, alerts, presets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-zinc-900 border-zinc-800 text-white"
              />
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800 text-white">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                <SelectItem value="all">All Categories</SelectItem>
                {CATEGORIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800 text-white">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                {SORT_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Category Quick Filters */}
          <div className="flex gap-2 flex-wrap">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <Button
                  key={cat.value}
                  variant="ghost"
                  size="sm"
                  className={`border ${
                    selectedCategory === cat.value
                      ? "bg-orange-500/10 border-orange-500/30 text-orange-400"
                      : "border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800/50"
                  }`}
                  onClick={() =>
                    setSelectedCategory(selectedCategory === cat.value ? "all" : cat.value)
                  }
                >
                  <Icon className="w-4 h-4 mr-1" />
                  {cat.label}
                </Button>
              );
            })}
          </div>

          {/* Item Grid */}
          {items.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {items.map((item) => (
                <Card
                  key={item.id}
                  className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors cursor-pointer group"
                  onClick={() => openItemDetail(item)}
                >
                  {/* Thumbnail */}
                  <div className="relative h-40 bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-t-lg overflow-hidden flex items-center justify-center">
                    {item.thumbnail_url ? (
                      <img src={item.thumbnail_url} alt={item.title} className="w-full h-full object-cover" />
                    ) : (
                      <Palette className="w-12 h-12 text-zinc-700" />
                    )}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                      <Eye className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="absolute top-2 right-2">
                      <CategoryBadge category={item.category} />
                    </div>
                  </div>
                  <CardContent className="p-4 space-y-2">
                    <h3 className="text-sm font-semibold text-white truncate">{item.title}</h3>
                    <p className="text-xs text-zinc-500 line-clamp-2">{item.description}</p>
                    <div className="flex items-center justify-between pt-1">
                      <span className={`text-sm font-bold ${item.price === 0 ? "text-emerald-400" : "text-orange-400"}`}>
                        {formatPrice(item.price)}
                      </span>
                      <div className="flex items-center gap-2">
                        <StarRating rating={item.rating_avg} count={item.rating_count} />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-zinc-500">
                      <span className="flex items-center gap-1">
                        <Download className="w-3 h-3" /> {item.download_count}
                      </span>
                      {item.tags.length > 0 && (
                        <span className="flex items-center gap-1">
                          <Tag className="w-3 h-3" /> {item.tags.slice(0, 2).join(", ")}
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-12 text-center">
                <Store className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No items found matching your filters.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ===== My Purchases Tab ===== */}
        <TabsContent value="purchases" className="space-y-4">
          {purchases.length > 0 ? (
            <div className="space-y-3">
              {purchases.map((p) => (
                <Card key={p.id} className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-zinc-800 flex items-center justify-center">
                        <Package className="w-6 h-6 text-zinc-500" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{p.title || "Item"}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          {p.category && <CategoryBadge category={p.category} />}
                          <span className="text-[10px] text-zinc-500">
                            Purchased {formatDate(p.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-orange-400">
                        {formatPrice(p.price_paid)}
                      </span>
                      {p.download_url && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-emerald-400 hover:text-emerald-300"
                          onClick={() => window.open(p.download_url!, "_blank")}
                        >
                          <Download className="w-4 h-4 mr-1" />
                          Download
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-12 text-center">
                <ShoppingCart className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">No purchases yet. Browse the marketplace to find something!</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ===== Seller Dashboard Tab ===== */}
        <TabsContent value="seller" className="space-y-4">
          {sellerProfile ? (
            <>
              {/* Seller Profile Card */}
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-orange-500/20 flex items-center justify-center">
                      <User className="w-6 h-6 text-orange-400" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-white">{sellerProfile.display_name}</p>
                      <p className="text-xs text-zinc-500">{sellerProfile.bio || "No bio set"}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <StarRating rating={sellerProfile.rating_avg} count={sellerProfile.rating_count} />
                        <span className="text-[10px] text-zinc-500">
                          {sellerProfile.total_sales} sales
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                    Active Seller
                  </Badge>
                </CardContent>
              </Card>

              {/* Add Item Button */}
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-zinc-300">Your Items ({sellerItems.length})</h3>
                <Button
                  size="sm"
                  className="bg-orange-500 hover:bg-orange-600 text-white"
                  onClick={() => setShowCreateItem(!showCreateItem)}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  New Item
                </Button>
              </div>

              {/* Create Item Form */}
              {showCreateItem && (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <Plus className="w-4 h-4" />
                      List New Item
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Title</Label>
                        <Input
                          placeholder="My Awesome Overlay Pack"
                          value={itemForm.title}
                          onChange={(e) => setItemForm({ ...itemForm, title: e.target.value })}
                          className="bg-zinc-800 border-zinc-700 text-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Category</Label>
                        <Select
                          value={itemForm.category}
                          onValueChange={(v) => setItemForm({ ...itemForm, category: v })}
                        >
                          <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-zinc-900 border-zinc-700">
                            {CATEGORIES.map((c) => (
                              <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Price (USD)</Label>
                        <Input
                          type="number"
                          placeholder="9.99"
                          value={itemForm.price}
                          onChange={(e) => setItemForm({ ...itemForm, price: e.target.value })}
                          className="bg-zinc-800 border-zinc-700 text-white"
                          min="0"
                          step="0.01"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Tags (comma-separated)</Label>
                        <Input
                          placeholder="neon, animated, overlay"
                          value={itemForm.tags}
                          onChange={(e) => setItemForm({ ...itemForm, tags: e.target.value })}
                          className="bg-zinc-800 border-zinc-700 text-white"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-300 text-sm">Description</Label>
                      <Textarea
                        placeholder="Describe your item..."
                        value={itemForm.description}
                        onChange={(e) => setItemForm({ ...itemForm, description: e.target.value })}
                        className="bg-zinc-800 border-zinc-700 text-white min-h-[80px]"
                      />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Preview URL</Label>
                        <Input
                          placeholder="https://..."
                          value={itemForm.preview_url}
                          onChange={(e) => setItemForm({ ...itemForm, preview_url: e.target.value })}
                          className="bg-zinc-800 border-zinc-700 text-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Download URL</Label>
                        <Input
                          placeholder="https://..."
                          value={itemForm.download_url}
                          onChange={(e) => setItemForm({ ...itemForm, download_url: e.target.value })}
                          className="bg-zinc-800 border-zinc-700 text-white"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Thumbnail URL</Label>
                        <Input
                          placeholder="https://..."
                          value={itemForm.thumbnail_url}
                          onChange={(e) => setItemForm({ ...itemForm, thumbnail_url: e.target.value })}
                          className="bg-zinc-800 border-zinc-700 text-white"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="sm" className="text-zinc-400" onClick={() => setShowCreateItem(false)}>
                        Cancel
                      </Button>
                      <Button size="sm" className="bg-orange-500 hover:bg-orange-600 text-white" onClick={createItem}>
                        Publish Item
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Seller Items List */}
              {sellerItems.length > 0 ? (
                <div className="space-y-3">
                  {sellerItems.map((item) => (
                    <Card key={item.id} className="bg-zinc-900/50 border-zinc-800">
                      <CardContent className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-lg bg-zinc-800 flex items-center justify-center">
                            <Palette className="w-6 h-6 text-zinc-500" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-white">{item.title}</p>
                              <Badge className={`text-[10px] ${
                                item.status === "published"
                                  ? "bg-emerald-500/20 text-emerald-400"
                                  : "bg-zinc-500/20 text-zinc-400"
                              }`}>
                                {item.status}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-3 mt-1 text-[10px] text-zinc-500">
                              <CategoryBadge category={item.category} />
                              <span>{formatPrice(item.price)}</span>
                              <span>{item.download_count} downloads</span>
                              <StarRating rating={item.rating_avg} count={item.rating_count} />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-zinc-400 hover:text-white"
                            onClick={() => openItemDetail(item)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-400 hover:text-red-300"
                            onClick={() => deleteSellerItem(item.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-8 text-center">
                    <Package className="w-10 h-10 text-zinc-700 mx-auto mb-2" />
                    <p className="text-sm text-zinc-500">No items listed yet. Create your first item!</p>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-8 text-center space-y-4">
                <Store className="w-16 h-16 text-zinc-700 mx-auto" />
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">Become a Seller</h3>
                  <p className="text-sm text-zinc-400 max-w-md mx-auto">
                    Create a seller profile to start listing overlays, alert packs, widget skins, and chatbot presets on the marketplace.
                  </p>
                </div>
                <Button
                  className="bg-orange-500 hover:bg-orange-600 text-white"
                  onClick={() => setShowSetupSeller(true)}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Set Up Seller Profile
                </Button>

                {showSetupSeller && (
                  <div className="text-left max-w-md mx-auto mt-4 space-y-4">
                    <Separator className="bg-zinc-800" />
                    <div className="space-y-2">
                      <Label className="text-zinc-300 text-sm">Display Name</Label>
                      <Input
                        placeholder="Your seller name"
                        value={sellerForm.display_name}
                        onChange={(e) => setSellerForm({ ...sellerForm, display_name: e.target.value })}
                        className="bg-zinc-800 border-zinc-700 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-300 text-sm">Bio</Label>
                      <Textarea
                        placeholder="Tell buyers about your creations..."
                        value={sellerForm.bio}
                        onChange={(e) => setSellerForm({ ...sellerForm, bio: e.target.value })}
                        className="bg-zinc-800 border-zinc-700 text-white min-h-[60px]"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-300 text-sm">Website (optional)</Label>
                      <Input
                        placeholder="https://yoursite.com"
                        value={sellerForm.website}
                        onChange={(e) => setSellerForm({ ...sellerForm, website: e.target.value })}
                        className="bg-zinc-800 border-zinc-700 text-white"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="sm" className="text-zinc-400" onClick={() => setShowSetupSeller(false)}>
                        Cancel
                      </Button>
                      <Button size="sm" className="bg-orange-500 hover:bg-orange-600 text-white" onClick={setupSeller}>
                        Create Profile
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ===== Revenue Tab ===== */}
        <TabsContent value="revenue" className="space-y-4">
          {sellerProfile && revenue ? (
            <>
              {/* Revenue Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <DollarSign className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs text-zinc-500 uppercase">Total Revenue</span>
                    </div>
                    <p className="text-2xl font-bold text-white">${revenue.total_revenue.toFixed(2)}</p>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-orange-400" />
                      <span className="text-xs text-zinc-500 uppercase">Net Revenue</span>
                    </div>
                    <p className="text-2xl font-bold text-white">${revenue.net_revenue.toFixed(2)}</p>
                    <p className="text-[10px] text-zinc-500 mt-1">After 20% platform fee</p>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <ShoppingCart className="w-4 h-4 text-blue-400" />
                      <span className="text-xs text-zinc-500 uppercase">Total Sales</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{revenue.total_sales}</p>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Star className="w-4 h-4 text-amber-400" />
                      <span className="text-xs text-zinc-500 uppercase">Avg Rating</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{revenue.avg_item_rating.toFixed(1)}</p>
                    <StarRating rating={revenue.avg_item_rating} />
                  </CardContent>
                </Card>
              </div>

              {/* Additional Stats */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-emerald-400" />
                      Revenue Breakdown
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">Gross Revenue</span>
                      <span className="text-white font-medium">${revenue.total_revenue.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">Platform Fees (20%)</span>
                      <span className="text-red-400">-${revenue.platform_fees.toFixed(2)}</span>
                    </div>
                    <Separator className="bg-zinc-800" />
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-300 font-medium">Net Revenue</span>
                      <span className="text-emerald-400 font-bold">${revenue.net_revenue.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">Pending Payout</span>
                      <span className="text-amber-400">${revenue.pending_payout.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">Items Listed</span>
                      <span className="text-white">{revenue.items_listed}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Top Items */}
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-orange-400" />
                      Top Selling Items
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {revenue.top_items.length > 0 ? (
                      <ScrollArea className="h-[200px]">
                        <div className="space-y-3">
                          {revenue.top_items.map((item, idx) => (
                            <div key={item.id} className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <span className="text-xs text-zinc-600 w-4">#{idx + 1}</span>
                                <div>
                                  <p className="text-sm text-white">{item.title}</p>
                                  <div className="flex items-center gap-2 mt-0.5">
                                    <CategoryBadge category={item.category} />
                                    <StarRating rating={item.rating_avg} />
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-sm font-medium text-orange-400">{formatPrice(item.price)}</p>
                                <p className="text-[10px] text-zinc-500">{item.download_count} sales</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    ) : (
                      <p className="text-sm text-zinc-500 text-center py-4">No sales yet</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-12 text-center">
                <BarChart3 className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">
                  Set up a seller profile to see revenue analytics.
                </p>
                <Button
                  size="sm"
                  className="mt-4 bg-orange-500 hover:bg-orange-600 text-white"
                  onClick={() => setActiveTab("seller")}
                >
                  Go to Seller Dashboard
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* ===== Item Detail Dialog ===== */}
      <Dialog open={!!selectedItem} onOpenChange={(open) => !open && setSelectedItem(null)}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-2xl max-h-[85vh] overflow-y-auto">
          {selectedItem && (
            <>
              <DialogHeader>
                <DialogTitle className="text-white flex items-center gap-2">
                  {selectedItem.title}
                  <CategoryBadge category={selectedItem.category} />
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                {/* Preview area */}
                <div className="relative h-48 bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-lg overflow-hidden flex items-center justify-center">
                  {selectedItem.preview_url || selectedItem.thumbnail_url ? (
                    <img
                      src={selectedItem.preview_url || selectedItem.thumbnail_url || ""}
                      alt={selectedItem.title}
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <Palette className="w-16 h-16 text-zinc-700" />
                  )}
                </div>

                <p className="text-sm text-zinc-300">{selectedItem.description}</p>

                {/* Tags */}
                {selectedItem.tags.length > 0 && (
                  <div className="flex gap-2 flex-wrap">
                    {selectedItem.tags.map((tag) => (
                      <Badge key={tag} className="bg-zinc-800 text-zinc-400 text-[10px]">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Stats & Price */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <StarRating rating={selectedItem.rating_avg} count={selectedItem.rating_count} />
                    <span className="text-xs text-zinc-500 flex items-center gap-1">
                      <Download className="w-3 h-3" /> {selectedItem.download_count} downloads
                    </span>
                  </div>
                  <span className={`text-xl font-bold ${selectedItem.price === 0 ? "text-emerald-400" : "text-orange-400"}`}>
                    {formatPrice(selectedItem.price)}
                  </span>
                </div>

                <Separator className="bg-zinc-800" />

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    className="flex-1 bg-orange-500 hover:bg-orange-600 text-white"
                    onClick={() => purchaseItem(selectedItem)}
                  >
                    <ShoppingCart className="w-4 h-4 mr-2" />
                    {selectedItem.price === 0 ? "Get Free" : `Buy for ${formatPrice(selectedItem.price)}`}
                  </Button>
                  <Button
                    variant="ghost"
                    className="text-zinc-400 hover:text-white"
                    onClick={() => {
                      setShowReviewDialog(true);
                    }}
                  >
                    <Pencil className="w-4 h-4 mr-1" />
                    Review
                  </Button>
                </div>

                {/* Reviews section */}
                {itemReviews.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-zinc-300">Reviews ({itemReviews.length})</h4>
                    <ScrollArea className="max-h-[200px]">
                      <div className="space-y-3">
                        {itemReviews.map((review) => (
                          <div key={review.id} className="bg-zinc-800/50 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center gap-2">
                                <StarRating rating={review.rating} />
                                <span className="text-[10px] text-zinc-500">{review.user_id}</span>
                              </div>
                              <span className="text-[10px] text-zinc-600">{formatDate(review.created_at)}</span>
                            </div>
                            {review.comment && (
                              <p className="text-xs text-zinc-400">{review.comment}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* ===== Review Dialog ===== */}
      <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Write a Review</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-zinc-300 text-sm">Rating</Label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((s) => (
                  <button
                    key={s}
                    onClick={() => setReviewForm({ ...reviewForm, rating: s })}
                    className="p-1 hover:scale-110 transition-transform"
                  >
                    <Star
                      className={`w-6 h-6 ${
                        s <= reviewForm.rating
                          ? "text-amber-400 fill-amber-400"
                          : "text-zinc-600"
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-zinc-300 text-sm">Comment (optional)</Label>
              <Textarea
                placeholder="Share your thoughts..."
                value={reviewForm.comment}
                onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                className="bg-zinc-800 border-zinc-700 text-white min-h-[80px]"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" className="text-zinc-400" onClick={() => setShowReviewDialog(false)}>
                Cancel
              </Button>
              <Button size="sm" className="bg-orange-500 hover:bg-orange-600 text-white" onClick={submitReview}>
                Submit Review
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
