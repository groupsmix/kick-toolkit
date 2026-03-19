import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
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
import { api } from "@/hooks/useApi";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import {
  Building2,
  Users,
  Palette,
  Settings,
  Plus,
  Trash2,
  Crown,
  Shield,
  Eye,
  UserPlus,
  Globe,
  Pencil,
  Check,
  X,
} from "lucide-react";

interface Organization {
  id: string;
  name: string;
  slug: string;
  owner_user_id: string;
  plan: string;
  status: string;
  max_members: number;
  custom_domain: string | null;
  created_at: string;
  updated_at: string;
}

interface OrgMember {
  id: string;
  org_id: string;
  user_id: string;
  username: string;
  role: string;
  channel: string | null;
  joined_at: string;
}

interface OrgBranding {
  org_id: string;
  logo_url: string | null;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  dark_mode: boolean;
  custom_css: string | null;
  welcome_message: string | null;
  updated_at: string | null;
}

const PLAN_CONFIG: Record<string, { label: string; color: string; bg: string; seats: number }> = {
  starter: { label: "Starter", color: "text-zinc-400", bg: "bg-zinc-500/10", seats: 5 },
  pro: { label: "Pro", color: "text-blue-400", bg: "bg-blue-500/10", seats: 25 },
  enterprise: { label: "Enterprise", color: "text-amber-400", bg: "bg-amber-500/10", seats: 100 },
};

const ROLE_CONFIG: Record<string, { icon: typeof Crown; color: string; label: string }> = {
  admin: { icon: Crown, color: "text-amber-400", label: "Admin" },
  manager: { icon: Shield, color: "text-blue-400", label: "Manager" },
  viewer: { icon: Eye, color: "text-zinc-400", label: "Viewer" },
};

export function WhiteLabelPage() {
  useAuth();

  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [branding, setBranding] = useState<OrgBranding | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showAddMember, setShowAddMember] = useState(false);
  const [editingBranding, setEditingBranding] = useState(false);

  const [createForm, setCreateForm] = useState({
    name: "",
    slug: "",
    plan: "starter",
    max_members: 5,
    custom_domain: "",
  });

  const [memberForm, setMemberForm] = useState({
    user_id: "",
    username: "",
    role: "viewer",
    channel: "",
  });

  const fetchOrgs = useCallback(async () => {
    try {
      const data = await api<Organization[]>("/api/whitelabel/orgs");
      setOrgs(data);
      if (data.length > 0 && !selectedOrg) {
        setSelectedOrg(data[0]);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load organizations";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [selectedOrg]);

  useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

  useEffect(() => {
    if (selectedOrg) {
      Promise.all([
        api<OrgMember[]>(`/api/whitelabel/orgs/${selectedOrg.id}/members`),
        api<OrgBranding>(`/api/whitelabel/orgs/${selectedOrg.id}/branding`),
      ]).then(([m, b]) => {
        setMembers(m);
        setBranding(b);
      }).catch(() => {
        setMembers([]);
        setBranding(null);
      });
    }
  }, [selectedOrg]);

  const createOrg = async () => {
    if (!createForm.name || !createForm.slug) {
      toast.error("Name and slug are required");
      return;
    }
    try {
      const org = await api<Organization>("/api/whitelabel/orgs", {
        method: "POST",
        body: JSON.stringify({
          name: createForm.name,
          slug: createForm.slug.toLowerCase().replace(/[^a-z0-9-]/g, "-"),
          plan: createForm.plan,
          max_members: createForm.max_members,
          custom_domain: createForm.custom_domain || null,
        }),
      });
      setOrgs((prev) => [org, ...prev]);
      setSelectedOrg(org);
      setShowCreateForm(false);
      setCreateForm({ name: "", slug: "", plan: "starter", max_members: 5, custom_domain: "" });
      toast.success("Organization created!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create organization");
    }
  };

  const deleteOrg = async (orgId: string) => {
    try {
      await api(`/api/whitelabel/orgs/${orgId}`, { method: "DELETE" });
      setOrgs((prev) => prev.filter((o) => o.id !== orgId));
      if (selectedOrg?.id === orgId) {
        setSelectedOrg(null);
        setMembers([]);
        setBranding(null);
      }
      toast.success("Organization deleted");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete organization");
    }
  };

  const addMember = async () => {
    if (!selectedOrg || !memberForm.user_id || !memberForm.username) {
      toast.error("User ID and username are required");
      return;
    }
    try {
      const member = await api<OrgMember>(`/api/whitelabel/orgs/${selectedOrg.id}/members`, {
        method: "POST",
        body: JSON.stringify({
          user_id: memberForm.user_id,
          username: memberForm.username,
          role: memberForm.role,
          channel: memberForm.channel || null,
        }),
      });
      setMembers((prev) => [...prev, member]);
      setShowAddMember(false);
      setMemberForm({ user_id: "", username: "", role: "viewer", channel: "" });
      toast.success("Member added!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add member");
    }
  };

  const removeMember = async (userId: string) => {
    if (!selectedOrg) return;
    try {
      await api(`/api/whitelabel/orgs/${selectedOrg.id}/members/${userId}`, { method: "DELETE" });
      setMembers((prev) => prev.filter((m) => m.user_id !== userId));
      toast.success("Member removed");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to remove member");
    }
  };

  const saveBranding = async () => {
    if (!selectedOrg || !branding) return;
    try {
      const updated = await api<OrgBranding>(`/api/whitelabel/orgs/${selectedOrg.id}/branding`, {
        method: "PUT",
        body: JSON.stringify({
          logo_url: branding.logo_url,
          primary_color: branding.primary_color,
          secondary_color: branding.secondary_color,
          accent_color: branding.accent_color,
          dark_mode: branding.dark_mode,
          custom_css: branding.custom_css,
          welcome_message: branding.welcome_message,
        }),
      });
      setBranding(updated);
      setEditingBranding(false);
      toast.success("Branding saved!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save branding");
    }
  };

  const formatDate = (ts: string) =>
    new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-cyan-500/20 via-teal-500/10 to-transparent border border-cyan-500/20 p-6">
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Building2 className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-bold text-white">White-Label Platform</h2>
              <Badge className="bg-cyan-500/20 text-cyan-400 border-cyan-500/30 text-[10px] uppercase font-bold">
                Enterprise
              </Badge>
            </div>
            <p className="text-zinc-400">
              Manage multiple streamers under your brand. Perfect for esports orgs and streamer agencies.
            </p>
          </div>
          <Button
            size="sm"
            className="bg-cyan-500 hover:bg-cyan-600 text-white"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            <Plus className="w-4 h-4 mr-1" />
            New Org
          </Button>
        </div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-10">
          <Building2 className="w-32 h-32 text-cyan-500" />
        </div>
      </div>

      {/* Create Org Form */}
      {showCreateForm && (
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Create Organization
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Organization Name</Label>
                <Input
                  placeholder="My Esports Org"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Slug (URL identifier)</Label>
                <Input
                  placeholder="my-esports-org"
                  value={createForm.slug}
                  onChange={(e) => setCreateForm({ ...createForm, slug: e.target.value })}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Plan</Label>
                <Select value={createForm.plan} onValueChange={(v) => setCreateForm({ ...createForm, plan: v })}>
                  <SelectTrigger className="bg-zinc-800 border-zinc-700 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-700">
                    <SelectItem value="starter">Starter (5 seats)</SelectItem>
                    <SelectItem value="pro">Pro (25 seats)</SelectItem>
                    <SelectItem value="enterprise">Enterprise (100 seats)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-300 text-sm">Custom Domain (optional)</Label>
                <Input
                  placeholder="dashboard.myorg.gg"
                  value={createForm.custom_domain}
                  onChange={(e) => setCreateForm({ ...createForm, custom_domain: e.target.value })}
                  className="bg-zinc-800 border-zinc-700 text-white"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" className="text-zinc-400" onClick={() => setShowCreateForm(false)}>
                Cancel
              </Button>
              <Button size="sm" className="bg-cyan-500 hover:bg-cyan-600 text-white" onClick={createOrg}>
                Create Organization
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Org Sidebar */}
        <div className="lg:col-span-1">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                Organizations
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {orgs.length > 0 ? (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-1 p-2">
                    {orgs.map((org) => {
                      const planConfig = PLAN_CONFIG[org.plan] || PLAN_CONFIG.starter;
                      return (
                        <button
                          key={org.id}
                          className={`w-full text-left p-3 rounded-lg transition-colors ${
                            selectedOrg?.id === org.id
                              ? "bg-cyan-500/10 border border-cyan-500/20"
                              : "hover:bg-zinc-800/50"
                          }`}
                          onClick={() => setSelectedOrg(org)}
                        >
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-white truncate">{org.name}</p>
                            <Badge className={`${planConfig.bg} ${planConfig.color} text-[10px]`}>
                              {planConfig.label}
                            </Badge>
                          </div>
                          <p className="text-[10px] text-zinc-500 mt-1">/{org.slug}</p>
                        </button>
                      );
                    })}
                  </div>
                </ScrollArea>
              ) : (
                <div className="p-6 text-center">
                  <Building2 className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500">No organizations yet. Create one to get started.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Org Detail */}
        <div className="lg:col-span-3">
          {selectedOrg ? (
            <Tabs defaultValue="members" className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">{selectedOrg.name}</h3>
                  <p className="text-xs text-zinc-500">Created {formatDate(selectedOrg.created_at)}</p>
                </div>
                <TabsList className="bg-zinc-900 border border-zinc-800">
                  <TabsTrigger value="members" className="data-[state=active]:bg-zinc-800">
                    <Users className="w-4 h-4 mr-1" />
                    Members
                  </TabsTrigger>
                  <TabsTrigger value="branding" className="data-[state=active]:bg-zinc-800">
                    <Palette className="w-4 h-4 mr-1" />
                    Branding
                  </TabsTrigger>
                  <TabsTrigger value="settings" className="data-[state=active]:bg-zinc-800">
                    <Settings className="w-4 h-4 mr-1" />
                    Settings
                  </TabsTrigger>
                </TabsList>
              </div>

              {/* Members Tab */}
              <TabsContent value="members" className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-zinc-400">
                    {members.length} / {selectedOrg.max_members} members
                  </p>
                  <Button
                    size="sm"
                    className="bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30"
                    onClick={() => setShowAddMember(!showAddMember)}
                  >
                    <UserPlus className="w-4 h-4 mr-1" />
                    Add Member
                  </Button>
                </div>

                {/* Add Member Form */}
                {showAddMember && (
                  <Card className="bg-zinc-800/50 border-zinc-700">
                    <CardContent className="p-4 space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-zinc-300 text-xs">User ID</Label>
                          <Input
                            placeholder="User ID..."
                            value={memberForm.user_id}
                            onChange={(e) => setMemberForm({ ...memberForm, user_id: e.target.value })}
                            className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-zinc-300 text-xs">Username</Label>
                          <Input
                            placeholder="Username..."
                            value={memberForm.username}
                            onChange={(e) => setMemberForm({ ...memberForm, username: e.target.value })}
                            className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-zinc-300 text-xs">Role</Label>
                          <Select value={memberForm.role} onValueChange={(v) => setMemberForm({ ...memberForm, role: v })}>
                            <SelectTrigger className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-900 border-zinc-700">
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="manager">Manager</SelectItem>
                              <SelectItem value="viewer">Viewer</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-zinc-300 text-xs">Channel (optional)</Label>
                          <Input
                            placeholder="Kick channel..."
                            value={memberForm.channel}
                            onChange={(e) => setMemberForm({ ...memberForm, channel: e.target.value })}
                            className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm" className="text-zinc-400 h-7" onClick={() => setShowAddMember(false)}>
                          Cancel
                        </Button>
                        <Button size="sm" className="bg-cyan-500 hover:bg-cyan-600 text-white h-7" onClick={addMember}>
                          Add Member
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Members List */}
                <div className="space-y-2">
                  {members.map((member) => {
                    const roleConfig = ROLE_CONFIG[member.role] || ROLE_CONFIG.viewer;
                    const RoleIcon = roleConfig.icon;
                    return (
                      <Card key={member.id} className="bg-zinc-900/50 border-zinc-800">
                        <CardContent className="p-3 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-zinc-800 ${roleConfig.color}`}>
                              <RoleIcon className="w-4 h-4" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-white">{member.username}</p>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className={`text-[10px] ${roleConfig.color} border-current/20`}>
                                  {roleConfig.label}
                                </Badge>
                                {member.channel && (
                                  <span className="text-[10px] text-zinc-500">#{member.channel}</span>
                                )}
                              </div>
                            </div>
                          </div>
                          {member.user_id !== selectedOrg?.owner_user_id && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-red-400 hover:text-red-300 h-8 w-8"
                              onClick={() => removeMember(member.user_id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </TabsContent>

              {/* Branding Tab */}
              <TabsContent value="branding" className="space-y-4">
                {branding && (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                          <Palette className="w-4 h-4 text-cyan-400" />
                          Brand Customization
                        </CardTitle>
                        {editingBranding ? (
                          <div className="flex gap-2">
                            <Button variant="ghost" size="sm" className="text-zinc-400 h-7" onClick={() => setEditingBranding(false)}>
                              <X className="w-3 h-3 mr-1" />
                              Cancel
                            </Button>
                            <Button size="sm" className="bg-cyan-500 hover:bg-cyan-600 text-white h-7" onClick={saveBranding}>
                              <Check className="w-3 h-3 mr-1" />
                              Save
                            </Button>
                          </div>
                        ) : (
                          <Button variant="ghost" size="sm" className="text-cyan-400 h-7" onClick={() => setEditingBranding(true)}>
                            <Pencil className="w-3 h-3 mr-1" />
                            Edit
                          </Button>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Color Preview */}
                      <div className="flex items-center gap-3">
                        <div className="flex gap-2">
                          <div
                            className="w-10 h-10 rounded-lg border border-zinc-700"
                            style={{ backgroundColor: branding.primary_color }}
                            title="Primary"
                          />
                          <div
                            className="w-10 h-10 rounded-lg border border-zinc-700"
                            style={{ backgroundColor: branding.secondary_color }}
                            title="Secondary"
                          />
                          <div
                            className="w-10 h-10 rounded-lg border border-zinc-700"
                            style={{ backgroundColor: branding.accent_color }}
                            title="Accent"
                          />
                        </div>
                        <div>
                          <p className="text-xs text-zinc-400">Brand Colors</p>
                          <p className="text-[10px] text-zinc-600">
                            {branding.primary_color} / {branding.secondary_color} / {branding.accent_color}
                          </p>
                        </div>
                      </div>

                      {editingBranding && (
                        <>
                          <Separator className="bg-zinc-800" />
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div className="space-y-2">
                              <Label className="text-zinc-300 text-xs">Primary Color</Label>
                              <div className="flex gap-2">
                                <input
                                  type="color"
                                  value={branding.primary_color}
                                  onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                                  className="w-8 h-8 rounded cursor-pointer"
                                />
                                <Input
                                  value={branding.primary_color}
                                  onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                                  className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm flex-1"
                                />
                              </div>
                            </div>
                            <div className="space-y-2">
                              <Label className="text-zinc-300 text-xs">Secondary Color</Label>
                              <div className="flex gap-2">
                                <input
                                  type="color"
                                  value={branding.secondary_color}
                                  onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                                  className="w-8 h-8 rounded cursor-pointer"
                                />
                                <Input
                                  value={branding.secondary_color}
                                  onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                                  className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm flex-1"
                                />
                              </div>
                            </div>
                            <div className="space-y-2">
                              <Label className="text-zinc-300 text-xs">Accent Color</Label>
                              <div className="flex gap-2">
                                <input
                                  type="color"
                                  value={branding.accent_color}
                                  onChange={(e) => setBranding({ ...branding, accent_color: e.target.value })}
                                  className="w-8 h-8 rounded cursor-pointer"
                                />
                                <Input
                                  value={branding.accent_color}
                                  onChange={(e) => setBranding({ ...branding, accent_color: e.target.value })}
                                  className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm flex-1"
                                />
                              </div>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <Label className="text-zinc-300 text-xs">Logo URL</Label>
                            <Input
                              placeholder="https://..."
                              value={branding.logo_url || ""}
                              onChange={(e) => setBranding({ ...branding, logo_url: e.target.value || null })}
                              className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label className="text-zinc-300 text-xs">Welcome Message</Label>
                            <Input
                              placeholder="Welcome to our dashboard!"
                              value={branding.welcome_message || ""}
                              onChange={(e) => setBranding({ ...branding, welcome_message: e.target.value || null })}
                              className="bg-zinc-800 border-zinc-700 text-white h-8 text-sm"
                            />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label className="text-zinc-300 text-sm">Dark Mode</Label>
                            <Switch
                              checked={branding.dark_mode}
                              onCheckedChange={(v) => setBranding({ ...branding, dark_mode: v })}
                            />
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Settings Tab */}
              <TabsContent value="settings" className="space-y-4">
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-sm text-zinc-400 flex items-center gap-2">
                      <Settings className="w-4 h-4 text-cyan-400" />
                      Organization Settings
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Organization Name</Label>
                        <p className="text-white text-sm">{selectedOrg.name}</p>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Slug</Label>
                        <p className="text-white text-sm font-mono">/{selectedOrg.slug}</p>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Plan</Label>
                        <Badge className={`${PLAN_CONFIG[selectedOrg.plan]?.bg || ""} ${PLAN_CONFIG[selectedOrg.plan]?.color || ""}`}>
                          {PLAN_CONFIG[selectedOrg.plan]?.label || selectedOrg.plan}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-zinc-300 text-sm">Max Members</Label>
                        <p className="text-white text-sm">{selectedOrg.max_members}</p>
                      </div>
                      {selectedOrg.custom_domain && (
                        <div className="space-y-2 sm:col-span-2">
                          <Label className="text-zinc-300 text-sm flex items-center gap-1">
                            <Globe className="w-3 h-3" />
                            Custom Domain
                          </Label>
                          <p className="text-white text-sm font-mono">{selectedOrg.custom_domain}</p>
                        </div>
                      )}
                    </div>

                    <Separator className="bg-zinc-800" />

                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-400 border-red-500/20 hover:bg-red-500/10"
                        onClick={() => deleteOrg(selectedOrg.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete Organization
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-12 text-center">
                <Building2 className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-zinc-400 text-sm">Select an organization or create a new one</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
