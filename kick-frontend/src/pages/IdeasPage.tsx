import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/hooks/useApi";
import {
  Lightbulb,
  Sparkles,
  Bookmark,
  BookmarkCheck,
  Trash2,
  Package,
  Download,
  Star,
  Gamepad2,
  CreditCard,
  DollarSign,
  Zap,
} from "lucide-react";

interface GiveawayIdea {
  id: string;
  title: string;
  description: string;
  category: string;
  estimated_cost: string;
  engagement_level: string;
  requirements: string[];
  saved: boolean;
}

interface Category {
  value: string;
  label: string;
  icon: string;
  count: number;
}

export function IdeasPage() {
  const [ideas, setIdeas] = useState<GiveawayIdea[]>([]);
  const [savedIdeas, setSavedIdeas] = useState<GiveawayIdea[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api<Category[]>("/api/ideas/categories").then(setCategories);
    api<GiveawayIdea[]>("/api/ideas/saved").then(setSavedIdeas);
    generateIdeas();
  }, []);

  const generateIdeas = async (category?: string) => {
    setLoading(true);
    const result = await api<GiveawayIdea[]>("/api/ideas/generate", {
      method: "POST",
      body: JSON.stringify({ category: category || null, budget: null, audience_size: null, game: null }),
    });
    setIdeas(result);
    setLoading(false);
  };

  const saveIdea = async (idea: GiveawayIdea) => {
    const saved = await api<GiveawayIdea>("/api/ideas/save", {
      method: "POST",
      body: JSON.stringify(idea),
    });
    setSavedIdeas([...savedIdeas, saved]);
    setIdeas(ideas.map((i) => (i.id === idea.id ? { ...i, saved: true } : i)));
  };

  const deleteSavedIdea = async (id: string) => {
    await api(`/api/ideas/saved/${id}`, { method: "DELETE" });
    setSavedIdeas(savedIdeas.filter((i) => i.id !== id));
  };

  const categoryIcon = (cat: string) => {
    switch (cat) {
      case "physical": return <Package className="w-4 h-4" />;
      case "digital": return <Download className="w-4 h-4" />;
      case "experience": return <Star className="w-4 h-4" />;
      case "in-game": return <Gamepad2 className="w-4 h-4" />;
      case "subscription": return <CreditCard className="w-4 h-4" />;
      default: return <Lightbulb className="w-4 h-4" />;
    }
  };

  const categoryColor = (cat: string) => {
    switch (cat) {
      case "physical": return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "digital": return "bg-purple-500/10 text-purple-400 border-purple-500/20";
      case "experience": return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "in-game": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "subscription": return "bg-pink-500/10 text-pink-400 border-pink-500/20";
      default: return "bg-zinc-500/10 text-zinc-400 border-zinc-500/20";
    }
  };

  const engagementColor = (level: string) => {
    if (level === "high") return "text-emerald-400";
    if (level === "medium") return "text-amber-400";
    return "text-zinc-400";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-400" />
            Stream Giveaway Ideas
          </h3>
          <p className="text-sm text-zinc-500">
            AI-generated giveaway ideas to boost engagement
          </p>
        </div>
        <Button
          onClick={() => generateIdeas(selectedCategory || undefined)}
          disabled={loading}
          className="bg-emerald-500 hover:bg-emerald-600 text-black"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
          ) : (
            <Sparkles className="w-4 h-4 mr-2" />
          )}
          Generate Ideas
        </Button>
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => { setSelectedCategory(null); generateIdeas(); }}
          className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
            !selectedCategory
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : "bg-zinc-900 text-zinc-400 border border-zinc-800 hover:border-zinc-700"
          }`}
        >
          All Categories
        </button>
        {categories.map((cat) => (
          <button
            key={cat.value}
            onClick={() => { setSelectedCategory(cat.value); generateIdeas(cat.value); }}
            className={`px-3 py-1.5 rounded-full text-sm flex items-center gap-1.5 transition-colors ${
              selectedCategory === cat.value
                ? `${categoryColor(cat.value)}`
                : "bg-zinc-900 text-zinc-400 border border-zinc-800 hover:border-zinc-700"
            }`}
          >
            {categoryIcon(cat.value)}
            {cat.label}
            <span className="text-zinc-600 text-xs">({cat.count})</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generated Ideas */}
        <div className="lg:col-span-2 space-y-4">
          <h4 className="text-sm font-medium text-zinc-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            Generated Ideas
          </h4>

          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-3">
              {ideas.map((idea) => (
                <Card key={idea.id} className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-white font-semibold">{idea.title}</h4>
                          <Badge className={`text-[10px] ${categoryColor(idea.category)}`}>
                            {categoryIcon(idea.category)}
                            <span className="ml-1">{idea.category}</span>
                          </Badge>
                        </div>
                        <p className="text-sm text-zinc-400 mb-3">{idea.description}</p>

                        <div className="flex items-center gap-4 text-xs">
                          <span className="flex items-center gap-1 text-zinc-500">
                            <DollarSign className="w-3 h-3" />
                            {idea.estimated_cost}
                          </span>
                          <span className={`flex items-center gap-1 ${engagementColor(idea.engagement_level)}`}>
                            <Zap className="w-3 h-3" />
                            {idea.engagement_level} engagement
                          </span>
                        </div>

                        {idea.requirements.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {idea.requirements.map((req) => (
                              <Badge key={req} variant="outline" className="text-[10px] border-zinc-700 text-zinc-500">
                                {req}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => saveIdea(idea)}
                        disabled={idea.saved}
                        className={idea.saved ? "text-emerald-400" : "text-zinc-500 hover:text-emerald-400"}
                      >
                        {idea.saved ? <BookmarkCheck className="w-5 h-5" /> : <Bookmark className="w-5 h-5" />}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Saved Ideas */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-zinc-400 flex items-center gap-2">
            <BookmarkCheck className="w-4 h-4 text-emerald-400" />
            Saved Ideas ({savedIdeas.length})
          </h4>

          {savedIdeas.length === 0 ? (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-6 text-center">
                <Bookmark className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
                <p className="text-sm text-zinc-500">No saved ideas yet</p>
                <p className="text-xs text-zinc-600 mt-1">Click the bookmark icon to save ideas</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {savedIdeas.map((idea) => (
                <Card key={idea.id} className="bg-zinc-900/50 border-zinc-800">
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h5 className="text-sm font-medium text-white">{idea.title}</h5>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge className={`text-[10px] ${categoryColor(idea.category)}`}>
                            {idea.category}
                          </Badge>
                          <span className="text-xs text-zinc-500">{idea.estimated_cost}</span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteSavedIdea(idea.id)}
                        className="text-zinc-500 hover:text-red-400 h-8 w-8"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
