import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import {
  Languages,
  Settings,
  Send,
  ArrowRight,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface Language {
  code: string;
  name: string;
}

interface TranslationSettings {
  channel: string;
  enabled: boolean;
  target_language: string;
  auto_translate: boolean;
  show_original: boolean;
}

interface TranslationResult {
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  was_translated: boolean;
  note?: string;
}

export function TranslationPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [settings, setSettings] = useState<TranslationSettings>({
    channel: "",
    enabled: false,
    target_language: "en",
    auto_translate: false,
    show_original: true,
  });
  const [languages, setLanguages] = useState<Language[]>([]);
  const [testText, setTestText] = useState("");
  const [testResult, setTestResult] = useState<TranslationResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<TranslationSettings>(`/api/translation/settings/${channel}`).then(setSettings),
      api<Language[]>("/api/translation/languages").then(setLanguages),
    ])
      .catch(() => toast.error("Failed to load translation settings"))
      .finally(() => setLoading(false));
  }, [channel]);

  const saveSettings = async () => {
    try {
      const result = await api<TranslationSettings>(`/api/translation/settings/${channel}`, {
        method: "POST",
        body: JSON.stringify(settings),
      });
      setSettings(result);
      toast.success("Translation settings saved");
    } catch {
      toast.error("Failed to save settings");
    }
  };

  const testTranslation = async () => {
    if (!testText.trim()) return;
    try {
      const result = await api<TranslationResult>("/api/translation/translate", {
        method: "POST",
        body: JSON.stringify({
          text: testText,
          target_language: settings.target_language,
        }),
      });
      setTestResult(result);
    } catch {
      toast.error("Translation failed");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Languages className="w-6 h-6 text-cyan-400" />
            Chat Translation
          </h2>
          <p className="text-sm text-zinc-500">Auto-translate chat messages for multilingual audiences</p>
        </div>
        <Badge className={settings.enabled ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700/50 text-zinc-400"}>
          {settings.enabled ? "Active" : "Disabled"}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Settings */}
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Settings className="w-5 h-5 text-emerald-400" />
              Translation Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white">Enable Translation</Label>
                <p className="text-xs text-zinc-500">Translate incoming chat messages</p>
              </div>
              <Switch
                checked={settings.enabled}
                onCheckedChange={(v) => setSettings({ ...settings, enabled: v })}
              />
            </div>

            <div>
              <Label className="text-zinc-400 text-xs">Target Language</Label>
              <select
                value={settings.target_language}
                onChange={(e) => setSettings({ ...settings, target_language: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-md text-white text-sm"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name} ({lang.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white">Auto-Translate</Label>
                <p className="text-xs text-zinc-500">Automatically translate all non-target messages</p>
              </div>
              <Switch
                checked={settings.auto_translate}
                onCheckedChange={(v) => setSettings({ ...settings, auto_translate: v })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white">Show Original</Label>
                <p className="text-xs text-zinc-500">Display original text alongside translation</p>
              </div>
              <Switch
                checked={settings.show_original}
                onCheckedChange={(v) => setSettings({ ...settings, show_original: v })}
              />
            </div>

            <Button onClick={saveSettings} className="bg-emerald-500 hover:bg-emerald-600 text-black w-full">
              Save Settings
            </Button>
          </CardContent>
        </Card>

        {/* Test Translation */}
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Send className="w-5 h-5 text-cyan-400" />
              Test Translation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-zinc-400 text-xs">Enter text to translate</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  value={testText}
                  onChange={(e) => setTestText(e.target.value)}
                  placeholder="Type a message in any language..."
                  className="bg-zinc-800 border-zinc-700 text-white"
                  onKeyDown={(e) => e.key === "Enter" && testTranslation()}
                />
                <Button onClick={testTranslation} className="bg-cyan-500 hover:bg-cyan-600 text-black">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {testResult && (
              <div className="p-4 bg-zinc-800/50 rounded-lg space-y-3">
                <div>
                  <span className="text-xs text-zinc-500 uppercase">Original ({testResult.source_language})</span>
                  <p className="text-white mt-1">{testResult.original_text}</p>
                </div>
                <div className="flex items-center justify-center">
                  <ArrowRight className="w-4 h-4 text-zinc-600" />
                </div>
                <div>
                  <span className="text-xs text-zinc-500 uppercase">Translated ({testResult.target_language})</span>
                  <p className="text-white mt-1">{testResult.translated_text}</p>
                </div>
                {testResult.note && (
                  <p className="text-xs text-amber-400 bg-amber-500/10 px-3 py-2 rounded">{testResult.note}</p>
                )}
                <Badge className={testResult.was_translated ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700/50 text-zinc-400"}>
                  {testResult.was_translated ? "Translated" : "Same language"}
                </Badge>
              </div>
            )}

            <div className="p-3 bg-zinc-800/30 rounded-lg">
              <h4 className="text-sm font-medium text-zinc-300 mb-2">Supported Languages</h4>
              <div className="flex flex-wrap gap-1">
                {languages.map((lang) => (
                  <Badge key={lang.code} variant="outline" className="text-[10px] border-zinc-700 text-zinc-500">
                    {lang.name}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
