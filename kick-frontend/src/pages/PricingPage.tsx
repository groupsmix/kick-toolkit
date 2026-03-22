import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Zap,
  Check,
  X,
  ArrowLeft,
  CreditCard,
  Bitcoin,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface PlanFeature {
  name: string;
  free: boolean | string;
  pro: boolean | string;
  premium: boolean | string;
}

const planFeatures: PlanFeature[] = [
  { name: "Dashboard Overview", free: true, pro: true, premium: true },
  { name: "Bot Commands", free: "20 commands", pro: "Unlimited", premium: "Unlimited" },
  { name: "Chat Log History", free: "1,000 entries", pro: "Unlimited", premium: "Unlimited" },
  { name: "Active Giveaways", free: "3 at a time", pro: "Unlimited", premium: "Unlimited" },
  { name: "AI Chat Moderation", free: "Basic", pro: true, premium: true },
  { name: "Chat Analytics", free: false, pro: true, premium: true },
  { name: "Giveaway Ideas Generator", free: true, pro: true, premium: true },
  { name: "Anti-Alt Detection", free: false, pro: false, premium: true },
  { name: "Tournament Organizer", free: false, pro: false, premium: true },
  { name: "Custom Alerts & Overlays", free: false, pro: false, premium: true },
  { name: "Advanced Analytics", free: false, pro: false, premium: true },
  { name: "API Access", free: false, pro: false, premium: true },
  { name: "Priority Support", free: false, pro: true, premium: true },
  { name: "Dedicated Support", free: false, pro: false, premium: true },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for getting started",
    popular: false,
  },
  {
    name: "Pro",
    price: "$9.99",
    period: "/month",
    description: "For growing streamers",
    popular: true,
  },
  {
    name: "Premium",
    price: "$24.99",
    period: "/month",
    description: "For professional streamers",
    popular: false,
  },
];

const faqs = [
  {
    question: "Can I change my plan later?",
    answer:
      "Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately and we'll prorate accordingly.",
  },
  {
    question: "What payment methods do you accept?",
    answer:
      "We accept all major credit cards through LemonSqueezy and cryptocurrency payments via NOWPayments (BTC, ETH, USDT, and more).",
  },
  {
    question: "Is there a free trial?",
    answer:
      "The Free plan is available forever with no credit card required. Pro and Premium plans come with a 7-day free trial.",
  },
  {
    question: "Can I cancel anytime?",
    answer:
      "Absolutely. You can cancel your subscription at any time. You'll keep access until the end of your billing period.",
  },
  {
    question: "Do you offer refunds?",
    answer:
      "Yes, we offer a 14-day money-back guarantee. If you're not satisfied, contact us for a full refund.",
  },
];

function FeatureCell({ value }: { value: boolean | string }) {
  if (typeof value === "string") {
    return <span className="text-sm text-zinc-300">{value}</span>;
  }
  return value ? (
    <Check className="w-5 h-5 text-emerald-400 mx-auto" />
  ) : (
    <X className="w-5 h-5 text-zinc-600 mx-auto" />
  );
}

export function PricingPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-zinc-950/80 backdrop-blur-xl border-b border-zinc-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => navigate("/")}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity"
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500">
                <Zap className="w-5 h-5 text-black" />
              </div>
              <span className="text-lg font-bold tracking-tight">KickTools</span>
            </button>
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                className="text-zinc-400 hover:text-white"
                onClick={() => navigate("/")}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
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

      {/* Header */}
      <section className="pt-16 pb-12 px-4 sm:px-6 lg:px-8 text-center">
        <Badge className="mb-6 bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-4 py-1.5">
          Pricing
        </Badge>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
          Choose Your Plan
        </h1>
        <p className="mt-4 text-lg text-zinc-400 max-w-xl mx-auto">
          Start free, upgrade when you need more. Simple pricing with no surprises.
        </p>
      </section>

      {/* Plan Cards */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`bg-zinc-900/80 transition-all duration-300 hover:scale-105 relative ${
                plan.popular
                  ? "border-emerald-500/50 ring-1 ring-emerald-500/30"
                  : "border-zinc-700"
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
                <p className="text-sm text-zinc-500 mt-1">{plan.description}</p>
                <div className="mt-4 mb-6">
                  <span className="text-4xl font-extrabold text-white">{plan.price}</span>
                  <span className="text-zinc-500 ml-1">{plan.period}</span>
                </div>
                <Button
                  className={`w-full font-semibold ${
                    plan.popular
                      ? "bg-emerald-500 hover:bg-emerald-600 text-black"
                      : "bg-zinc-800 hover:bg-zinc-700 text-white"
                  }`}
                  onClick={login}
                >
                  {plan.price === "$0" ? "Get Started Free" : `Start ${plan.name} Trial`}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Payment Methods */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 border-y border-zinc-800/50 bg-zinc-900/30">
        <div className="max-w-3xl mx-auto text-center">
          <h3 className="text-lg font-semibold text-white mb-4">
            Flexible Payment Options
          </h3>
          <div className="flex items-center justify-center gap-8">
            <div className="flex items-center gap-2 text-zinc-400">
              <CreditCard className="w-5 h-5" />
              <span className="text-sm">Credit / Debit Card</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <Bitcoin className="w-5 h-5" />
              <span className="text-sm">Crypto (BTC, ETH, USDT)</span>
            </div>
          </div>
          <p className="text-xs text-zinc-600 mt-3">
            Card payments via LemonSqueezy • Crypto via NOWPayments
          </p>
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-10">
            Feature Comparison
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="py-4 px-4 text-left text-sm font-medium text-zinc-400">
                    Feature
                  </th>
                  {plans.map((plan) => (
                    <th
                      key={plan.name}
                      className={`py-4 px-4 text-center text-sm font-medium ${
                        plan.popular ? "text-emerald-400" : "text-zinc-400"
                      }`}
                    >
                      {plan.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {planFeatures.map((feature) => (
                  <tr
                    key={feature.name}
                    className="border-b border-zinc-800/50 hover:bg-zinc-900/30"
                  >
                    <td className="py-3 px-4 text-sm text-zinc-300">
                      {feature.name}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <FeatureCell value={feature.free} />
                    </td>
                    <td className="py-3 px-4 text-center">
                      <FeatureCell value={feature.pro} />
                    </td>
                    <td className="py-3 px-4 text-center">
                      <FeatureCell value={feature.premium} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-zinc-900/30">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-10">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq) => (
              <Card key={faq.question} className="bg-zinc-900/80 border-zinc-800">
                <CardContent className="p-6">
                  <h3 className="text-sm font-semibold text-white mb-2">
                    {faq.question}
                  </h3>
                  <p className="text-sm text-zinc-400">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-zinc-600">
            &copy; {new Date().getFullYear()} KickTools. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/terms")}
              className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors"
            >
              Terms
            </button>
            <button
              onClick={() => navigate("/privacy")}
              className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors"
            >
              Privacy
            </button>
            <button
              onClick={() => navigate("/disclaimer")}
              className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors"
            >
              Disclaimer
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
