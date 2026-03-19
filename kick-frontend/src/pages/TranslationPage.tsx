import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { api } from "@/hooks/useApi";
import { toast } from "sonner";
import { Languages } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface TranslationSettings {
  channel: string;
  enabled: boolean;
  target_language: string;
  source_languages: string[];
}

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "pt", name: "Portuguese" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese" },
  { code: "ru", name: "Russian" },
  { code: "ar", name: "Arabic" },
];

export function TranslationPage() {
  const { user } = useAuth();
  const channel = user?.streamer_channel || user?.name || "";
  const [settings, setSettings] = useState<TranslationSettings>({
    channel,
    enabled: false,
    target_language: "en",
    source_languages: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<TranslationSettings>(`/api/translation/settings/${channel}`)
      .then((s) => setSettings(s))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [channel]);

  const save = async () => {
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

  const toggleLanguage = (code: string) => {
    const langs = settings.source_languages.includes(code)
      ? settings.source_languages.filter((l) => l !== code)
      : [...settings.source_languages, code];
    setSettings({ ...settings, source_languages: langs });
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
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Languages className="w-6 h-6 text-cyan-400" />
          Chat Translation
        </h2>
        <p className="text-sm text-zinc-500">Auto-translate chat messages from other languages</p>
      </div>

      <Card className="bg-zinc-900/50 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-sm text-white flex items-center justify-between">
            Translation Settings
            <Switch checked={settings.enabled} onCheckedChange={(v) => setSettings({ ...settings, enabled: v })} />
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-zinc-400 text-xs">Target Language</Label>
            <select
              value={settings.target_language}
              onChange={(e) => setSettings({ ...settings, target_language: e.target.value })}
              className="w-full h-10 rounded-md border border-zinc-700 bg-zinc-800 text-white px-3 text-sm"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.name}</option>
              ))}
            </select>
          </div>
          <div>
            <Label className="text-zinc-400 text-xs mb-2 block">Source Languages to Translate</Label>
            <div className="flex flex-wrap gap-2">
              {LANGUAGES.filter((l) => l.code !== settings.target_language).map((l) => (
                <button
                  key={l.code}
                  onClick={() => toggleLanguage(l.code)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    settings.source_languages.includes(l.code)
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-zinc-900 border-zinc-700 text-zinc-400 hover:border-zinc-600"
                  }`}
                >
                  {l.name}
                </button>
              ))}
            </div>
          </div>
          <Button onClick={save} className="bg-emerald-500 hover:bg-emerald-600 text-black">
            Save Settings
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
