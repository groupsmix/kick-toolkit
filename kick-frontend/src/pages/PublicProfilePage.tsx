import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  User,
  Calendar,
  Clock,
  ExternalLink,
  Gamepad2,
  Zap,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ProfileData {
  profile: {
    channel: string;
    display_name: string;
    bio: string;
    avatar_url: string | null;
    banner_url: string | null;
    social_links: Record<string, string>;
    is_public: boolean;
    theme_color: string;
    total_followers: number;
  };
  schedule: Array<{
    id: string;
    day_of_week: number;
    start_time: string;
    end_time: string;
    title: string;
    game: string;
    enabled: boolean;
  }>;
}

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function PublicProfilePage() {
  const { channel } = useParams<{ channel: string }>();
  const [data, setData] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!channel) return;
    setLoading(true);
    fetch(`${API_URL}/api/profiles/public/${channel}`)
      .then(async (res) => {
        if (!res.ok) throw new Error("Profile not found");
        return res.json();
      })
      .then(setData)
      .catch((err) => {
        setError(err.message);
        toast.error("Failed to load profile");
      })
      .finally(() => setLoading(false));
  }, [channel]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <Card className="bg-zinc-900/50 border-zinc-800 max-w-md mx-auto">
          <CardContent className="p-8 text-center">
            <User className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
            <h2 className="text-xl font-bold text-white mb-2">Profile Not Found</h2>
            <p className="text-zinc-500 text-sm">This streamer profile doesn&apos;t exist or is not public.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { profile, schedule } = data;
  const enabledSchedule = schedule.filter((s) => s.enabled).sort((a, b) => a.day_of_week - b.day_of_week);
  const themeColor = profile.theme_color || "#10b981";

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Banner */}
      <div className="h-48 relative" style={{ background: profile.banner_url ? `url(${profile.banner_url}) center/cover` : `linear-gradient(135deg, ${themeColor}22, ${themeColor}44)` }}>
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-zinc-950" />
      </div>

      <div className="max-w-3xl mx-auto px-4 -mt-16 relative">
        {/* Profile header */}
        <div className="flex items-end gap-4 mb-6">
          <div className="w-24 h-24 rounded-full border-4 border-zinc-950 overflow-hidden" style={{ background: `${themeColor}33` }}>
            {profile.avatar_url ? (
              <img src={profile.avatar_url} alt={profile.display_name || profile.channel} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <User className="w-10 h-10" style={{ color: themeColor }} />
              </div>
            )}
          </div>
          <div className="flex-1 pb-1">
            <h1 className="text-2xl font-bold text-white">{profile.display_name || profile.channel}</h1>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-zinc-500 text-sm">@{profile.channel}</span>
              {profile.total_followers > 0 && (
                <Badge variant="outline" className="border-zinc-700 text-zinc-400 text-xs">
                  {profile.total_followers.toLocaleString()} followers
                </Badge>
              )}
            </div>
          </div>
          <Button
            className="text-black font-semibold"
            style={{ backgroundColor: themeColor }}
            onClick={() => window.open(`https://kick.com/${profile.channel}`, "_blank")}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Watch on Kick
          </Button>
        </div>

        {/* Bio */}
        {profile.bio && (
          <Card className="bg-zinc-900/50 border-zinc-800 mb-6">
            <CardContent className="p-4">
              <p className="text-zinc-300 text-sm whitespace-pre-wrap">{profile.bio}</p>
            </CardContent>
          </Card>
        )}

        {/* Social Links */}
        {Object.keys(profile.social_links).length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {Object.entries(profile.social_links).map(([platform, url]) => (
              <Button
                key={platform}
                variant="outline"
                size="sm"
                className="border-zinc-700 text-zinc-400 hover:text-white text-xs capitalize"
                onClick={() => window.open(url, "_blank")}
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                {platform}
              </Button>
            ))}
          </div>
        )}

        {/* Schedule */}
        <Card className="bg-zinc-900/50 border-zinc-800 mb-6">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2 text-lg">
              <Calendar className="w-5 h-5" style={{ color: themeColor }} />
              Stream Schedule
            </CardTitle>
          </CardHeader>
          <CardContent>
            {enabledSchedule.length === 0 ? (
              <p className="text-zinc-600 text-sm text-center py-4">No schedule set</p>
            ) : (
              <div className="space-y-2">
                {enabledSchedule.map((entry) => (
                  <div key={entry.id} className="flex items-center gap-3 p-3 rounded-lg bg-zinc-800/50">
                    <Badge variant="outline" className="border-zinc-700 text-zinc-400 w-12 justify-center text-xs">
                      {DAY_NAMES[entry.day_of_week]}
                    </Badge>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-zinc-500" />
                      <span className="text-sm text-zinc-300 font-mono">{entry.start_time} - {entry.end_time}</span>
                    </div>
                    {entry.title && <span className="text-sm text-white">{entry.title}</span>}
                    {entry.game && (
                      <div className="flex items-center gap-1 ml-auto">
                        <Gamepad2 className="w-3.5 h-3.5 text-zinc-500" />
                        <span className="text-xs text-zinc-500">{entry.game}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center py-8">
          <div className="flex items-center justify-center gap-2 text-zinc-600 text-xs">
            <Zap className="w-3 h-3" />
            <span>Powered by KickTools</span>
          </div>
        </div>
      </div>
    </div>
  );
}
