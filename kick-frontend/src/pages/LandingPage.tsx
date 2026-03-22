import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Zap,
  Bot,
  MessageSquare,
  Gift,
  ShieldAlert,
  Trophy,
  Lightbulb,
  Check,
  ArrowRight,
  Users,
  Shield,
  ExternalLink,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

const features = [
  {
    icon: Bot,
    title: "Chat Bot & AI Moderation",
    description:
      "Custom commands, auto-mod rules, and AI-powered toxicity detection to keep your chat clean.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
  },
  {
    icon: MessageSquare,
    title: "Chat Logs & Search",
    description:
      "Searchable, filterable chat history with user profiles and top chatters analytics.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Gift,
    title: "Giveaway Roller",
    description:
      "Create giveaways with keyword entry, animated winner rolling, and reroll support.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    icon: ShieldAlert,
    title: "Anti-Alt Detection",
    description:
      "AI-powered alt account detection with risk scoring and automatic actions.",
    color: "text-red-400",
    bg: "bg-red-500/10",
  },
  {
    icon: Trophy,
    title: "Tournament Organizer",
    description:
      "Keyword-based registration, auto-bracket generation, and match management.",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  {
    icon: Lightbulb,
    title: "Stream Giveaway Ideas",
    description:
      "Categorized idea generator with save and bookmark functionality for future streams.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Get started with the basics",
    features: [
      "Dashboard overview",
      "20 bot commands",
      "1,000 chat log entries",
      "3 active giveaways",
      "Community support",
    ],
    cta: "Get Started",
    popular: false,
    color: "border-zinc-700",
  },
  {
    name: "Pro",
    price: "$9.99",
    period: "/month",
    description: "Everything you need to grow",
    features: [
      "Everything in Free",
      "Unlimited bot commands",
      "Unlimited chat logs",
      "AI moderation",
      "Unlimited giveaways",
      "Chat analytics",
      "Priority support",
    ],
    cta: "Start Pro Trial",
    popular: true,
    color: "border-emerald-500/50",
  },
  {
    name: "Premium",
    price: "$24.99",
    period: "/month",
    description: "For serious streamers",
    features: [
      "Everything in Pro",
      "Anti-alt detection",
      "Tournament organizer",
      "Custom alerts & overlays",
      "Advanced analytics",
      "API access",
      "Dedicated support",
    ],
    cta: "Go Premium",
    popular: false,
    color: "border-zinc-700",
  },
];

const howItWorks = [
  {
    step: "1",
    title: "Connect Your Kick Account",
    description: "Sign in with Kick OAuth in one click. We never store your password.",
  },
  {
    step: "2",
    title: "Configure Your Tools",
    description: "Set up bot commands, moderation rules, and giveaway preferences from your dashboard.",
  },
  {
    step: "3",
    title: "Go Live & Relax",
    description: "Your toolkit works in the background — moderating chat, running giveaways, and tracking analytics automatically.",
  },
];

export function LandingPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-zinc-950/80 backdrop-blur-xl border-b border-zinc-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500">
                <Zap className="w-5 h-5 text-black" />
              </div>
              <span className="text-lg font-bold tracking-tight">
                KickTools
              </span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a
                href="#features"
                className="text-sm text-zinc-400 hover:text-white transition-colors"
              >
                Features
              </a>
              <a
                href="#pricing"
                className="text-sm text-zinc-400 hover:text-white transition-colors"
              >
                Pricing
              </a>
              <a
                href="#preview"
                className="text-sm text-zinc-400 hover:text-white transition-colors"
              >
                Preview
              </a>
              <button
                onClick={() => navigate("/terms")}
                className="text-sm text-zinc-400 hover:text-white transition-colors"
              >
                Legal
              </button>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                className="text-zinc-400 hover:text-white"
                onClick={login}
              >
                Log In
              </Button>
              <Button
                className="bg-emerald-500 hover:bg-emerald-600 text-black font-semibold"
                onClick={login}
              >
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 via-transparent to-transparent" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="relative max-w-4xl mx-auto text-center">
          <Badge className="mb-6 bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-4 py-1.5">
            Built for Kick Streamers
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            Supercharge Your{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-emerald-600">
              Kick Stream
            </span>
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            Chat bot, AI moderation, giveaways, tournaments, anti-alt detection,
            and more — all in one powerful dashboard built for Kick streamers.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              className="w-full sm:w-auto bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-base px-8 py-6"
              onClick={login}
            >
              <ExternalLink className="w-5 h-5 mr-2" />
              Connect with Kick — It's Free
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="w-full sm:w-auto border-zinc-700 text-zinc-300 hover:text-white hover:border-zinc-500 px-8 py-6"
              onClick={() => navigate("/pricing")}
            >
              View Pricing
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
          <div className="mt-8 flex items-center justify-center gap-6 text-sm text-zinc-500">
            <span className="flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-400" />
              Free tier available
            </span>
            <span className="flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-400" />
              No credit card required
            </span>
            <span className="flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-400" />
              Cancel anytime
            </span>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 border-y border-zinc-800/50 bg-zinc-900/30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <Badge className="mb-4 bg-zinc-700/50 text-zinc-300 border-zinc-600/30">
              How It Works
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold">
              Up and Running in Minutes
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {howItWorks.map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                  <span className="text-lg font-bold text-emerald-400">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-blue-500/10 text-blue-400 border-blue-500/20">
              Features
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold">
              Everything You Need to{" "}
              <span className="text-emerald-400">Grow</span>
            </h2>
            <p className="mt-4 text-zinc-400 max-w-xl mx-auto">
              Powerful tools designed specifically for Kick streamers to engage
              their audience and manage their community.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card
                  key={feature.title}
                  className="bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 transition-all duration-300 group"
                >
                  <CardContent className="p-6">
                    <div
                      className={`w-12 h-12 rounded-xl ${feature.bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
                    >
                      <Icon className={`w-6 h-6 ${feature.color}`} />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section
        id="pricing"
        className="py-20 px-4 sm:px-6 lg:px-8 bg-zinc-900/30"
      >
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              Pricing
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold">
              Simple, Transparent Pricing
            </h2>
            <p className="mt-4 text-zinc-400 max-w-xl mx-auto">
              Start free and upgrade as you grow. No hidden fees, cancel
              anytime.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {plans.map((plan) => (
              <Card
                key={plan.name}
                className={`bg-zinc-900/80 ${plan.color} transition-all duration-300 hover:scale-105 relative ${
                  plan.popular ? "ring-1 ring-emerald-500/30" : ""
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-emerald-500 text-black font-bold px-3">
                      Most Popular
                    </Badge>
                  </div>
                )}
                <CardContent className="p-6 pt-8">
                  <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                  <p className="text-sm text-zinc-500 mt-1">
                    {plan.description}
                  </p>
                  <div className="mt-4 mb-6">
                    <span className="text-4xl font-extrabold text-white">
                      {plan.price}
                    </span>
                    <span className="text-zinc-500 ml-1">{plan.period}</span>
                  </div>
                  <Button
                    className={`w-full font-semibold ${
                      plan.popular
                        ? "bg-emerald-500 hover:bg-emerald-600 text-black"
                        : "bg-zinc-800 hover:bg-zinc-700 text-white"
                    }`}
                    onClick={() =>
                      plan.price === "$0" ? login() : navigate("/pricing")
                    }
                  >
                    {plan.cta}
                  </Button>
                  <ul className="mt-6 space-y-3">
                    {plan.features.map((feature) => (
                      <li
                        key={feature}
                        className="flex items-start gap-2 text-sm text-zinc-300"
                      >
                        <Check className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Product Preview Section */}
      <section id="preview" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-500/10 text-purple-400 border-purple-500/20">
              Product Preview
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold">
              See What You Get
            </h2>
            <p className="mt-4 text-zinc-400 max-w-xl mx-auto">
              A powerful dashboard packed with tools to manage and grow your Kick stream.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Bot className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-lg font-semibold text-white">Smart Chat Bot</h3>
                </div>
                <p className="text-sm text-zinc-400 mb-4">Custom commands with variables, timed messages, welcome messages, shoutouts, and AI-powered moderation — all configurable from one panel.</p>
                <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50 space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <code className="text-emerald-400 font-mono">!socials</code>
                    <span className="text-zinc-500">&rarr;</span>
                    <span className="text-zinc-300">Follow me on Twitter and Instagram!</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <code className="text-emerald-400 font-mono">!lurk</code>
                    <span className="text-zinc-500">&rarr;</span>
                    <span className="text-zinc-300">{'{username}'} is now lurking!</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Gift className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-lg font-semibold text-white">Giveaway Roller</h3>
                </div>
                <p className="text-sm text-zinc-400 mb-4">Keyword-based entry, animated winner selection, sub/follower-only modes, manual entries, and one-click rerolls.</p>
                <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50 text-center">
                  <p className="text-xs text-zinc-500 mb-1">Winner</p>
                  <p className="text-2xl font-bold text-emerald-400 animate-pulse">viewer_jenny</p>
                  <p className="text-xs text-zinc-600 mt-2">5 entries &middot; Keyword: !enter</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-3">
                  <ShieldAlert className="w-5 h-5 text-red-400" />
                  <h3 className="text-lg font-semibold text-white">AI Moderation</h3>
                </div>
                <p className="text-sm text-zinc-400 mb-4">AI toxicity detection, spam filters, caps lock filters, link filters, and banned word lists — all working together automatically.</p>
                <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-300">"FREE VIEWERS AT bit.ly/scam"</span>
                    <Badge className="bg-red-500/20 text-red-400 border-red-500/20 text-[10px]">Blocked</Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-300">"GG great play!"</span>
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/20 text-[10px]">Clean</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Trophy className="w-5 h-5 text-amber-400" />
                  <h3 className="text-lg font-semibold text-white">Tournament Organizer</h3>
                </div>
                <p className="text-sm text-zinc-400 mb-4">Auto-bracket generation, keyword registration, match management, and live bracket visualization.</p>
                <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-white font-medium">Friday Night Fights</span>
                    <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/20 text-[10px]">Round 2</Badge>
                  </div>
                  <p className="text-xs text-zinc-500">8 players &middot; Single elimination &middot; Street Fighter 6</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-zinc-900/50 to-zinc-950">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Ready to Level Up Your Stream?
          </h2>
          <p className="text-zinc-400 mb-8 text-lg">
            Start streaming smarter today — connect your Kick account and
            unlock powerful tools for free.
          </p>
          <Button
            size="lg"
            className="bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-base px-10 py-6"
            onClick={login}
          >
            <Zap className="w-5 h-5 mr-2" />
            Start For Free
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500">
                  <Zap className="w-5 h-5 text-black" />
                </div>
                <span className="text-lg font-bold">KickTools</span>
              </div>
              <p className="text-sm text-zinc-500">
                The ultimate streamer toolkit for Kick.com
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">Product</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#features"
                    className="text-sm text-zinc-500 hover:text-white transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <button
                    onClick={() => navigate("/pricing")}
                    className="text-sm text-zinc-500 hover:text-white transition-colors"
                  >
                    Pricing
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">Legal</h4>
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() => navigate("/terms")}
                    className="text-sm text-zinc-500 hover:text-white transition-colors"
                  >
                    Terms of Service
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => navigate("/privacy")}
                    className="text-sm text-zinc-500 hover:text-white transition-colors"
                  >
                    Privacy Policy
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => navigate("/disclaimer")}
                    className="text-sm text-zinc-500 hover:text-white transition-colors"
                  >
                    Disclaimer
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">
                Community
              </h4>
              <ul className="space-y-2">
                <li>
                  <span className="flex items-center gap-1.5 text-sm text-zinc-500">
                    <Users className="w-3.5 h-3.5" />
                    Discord (coming soon)
                  </span>
                </li>
                <li>
                  <span className="flex items-center gap-1.5 text-sm text-zinc-500">
                    <Shield className="w-3.5 h-3.5" />
                    Support
                  </span>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-zinc-600">
              &copy; {new Date().getFullYear()} KickTools. All rights reserved.
            </p>
            <p className="text-xs text-zinc-600">
              Not affiliated with Kick.com or Kick Streaming Pty Ltd.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
