import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Zap, ArrowLeft } from "lucide-react";

function GoBack() {
  const navigate = useNavigate();
  return (
    <Button
      variant="ghost"
      className="text-zinc-400 hover:text-white"
      onClick={() => navigate("/")}
    >
      <ArrowLeft className="w-4 h-4 mr-2" />
      Back
    </Button>
  );
}

export function TermsPage() {
  const navigate = useNavigate();

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
            <GoBack />
          </div>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h1 className="text-3xl font-bold mb-2">Terms of Service</h1>
        <p className="text-sm text-zinc-500 mb-8">
          Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
        </p>

        <div className="prose prose-invert prose-zinc max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-white mb-3">1. Acceptance of Terms</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              By accessing or using KickTools ("the Service"), you agree to be bound by these Terms of Service ("Terms").
              If you do not agree to these Terms, you may not access or use the Service. These Terms apply to all visitors,
              users, and others who access or use the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">2. Description of Service</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              KickTools provides a suite of tools for Kick.com streamers, including but not limited to: dashboard analytics,
              chat bot management, AI-powered moderation, giveaway management, tournament organization, and anti-alt account
              detection. The Service is provided "as is" and may be modified, updated, or discontinued at any time.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">3. User Accounts</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              To use the Service, you must authenticate via Kick.com OAuth. You are responsible for maintaining the security
              of your account and all activities under it. You must be at least 13 years old to use the Service. You agree to
              provide accurate information and keep your account details current.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">4. Subscription Plans & Payments</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              KickTools offers Free, Pro, and Premium subscription plans. Paid subscriptions are billed monthly through our
              payment processors (LemonSqueezy for card payments, NOWPayments for cryptocurrency). By subscribing, you
              authorize recurring charges. You may cancel at any time; access continues until the end of the billing period.
            </p>
            <ul className="list-disc list-inside text-sm text-zinc-400 mt-3 space-y-1">
              <li>Prices are in USD and may be subject to applicable taxes.</li>
              <li>We reserve the right to change pricing with 30 days notice.</li>
              <li>Refunds are available within 14 days of initial purchase.</li>
              <li>Failed payments may result in temporary suspension of premium features.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">5. Acceptable Use</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">You agree not to:</p>
            <ul className="list-disc list-inside text-sm text-zinc-400 mt-3 space-y-1">
              <li>Use the Service for any unlawful purpose or in violation of Kick.com's Terms of Service.</li>
              <li>Attempt to gain unauthorized access to any part of the Service.</li>
              <li>Interfere with or disrupt the Service or servers connected to it.</li>
              <li>Reverse engineer, decompile, or disassemble any part of the Service.</li>
              <li>Use the Service to harass, abuse, or harm other users.</li>
              <li>Resell or redistribute the Service without written permission.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">6. Intellectual Property</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              The Service and its original content, features, and functionality are owned by KickTools and are protected by
              international copyright, trademark, and other intellectual property laws. You retain ownership of any content
              you create using the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">7. Third-Party Services</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              The Service integrates with third-party services including Kick.com, OpenAI, LemonSqueezy, and NOWPayments.
              Your use of these services is governed by their respective terms. We are not responsible for the availability,
              accuracy, or content of third-party services.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">8. Limitation of Liability</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              In no event shall KickTools, its directors, employees, partners, agents, suppliers, or affiliates be liable for
              any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of
              profits, data, use, goodwill, or other intangible losses, resulting from your access to or use of (or inability
              to access or use) the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">9. Termination</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              We may terminate or suspend your access to the Service immediately, without prior notice or liability, for any
              reason, including breach of these Terms. Upon termination, your right to use the Service will immediately cease.
              All provisions of the Terms which by their nature should survive termination shall survive.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">10. Changes to Terms</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              We reserve the right to modify these Terms at any time. We will provide notice of significant changes by posting
              the updated Terms on this page with an updated "Last updated" date. Your continued use of the Service after
              changes constitutes acceptance of the modified Terms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">11. Contact Us</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              If you have questions about these Terms, please contact us at{" "}
              <span className="text-emerald-400">support@kicktools.app</span>.
            </p>
          </section>
        </div>

        {/* Footer Links */}
        <div className="mt-12 pt-8 border-t border-zinc-800 flex items-center gap-4">
          <button onClick={() => navigate("/privacy")} className="text-sm text-zinc-500 hover:text-white transition-colors">
            Privacy Policy
          </button>
          <span className="text-zinc-700">•</span>
          <button onClick={() => navigate("/disclaimer")} className="text-sm text-zinc-500 hover:text-white transition-colors">
            Disclaimer
          </button>
        </div>
      </div>
    </div>
  );
}
