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

export function PrivacyPage() {
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
        <h1 className="text-3xl font-bold mb-2">Privacy Policy</h1>
        <p className="text-sm text-zinc-500 mb-8">
          Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
        </p>

        <div className="prose prose-invert prose-zinc max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-white mb-3">1. Introduction</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              KickTools ("we," "our," or "us") respects your privacy and is committed to protecting your personal data.
              This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our
              Service. Please read this policy carefully. By using KickTools, you consent to the practices described herein.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">2. Information We Collect</h2>
            <p className="text-sm text-zinc-400 leading-relaxed mb-3">
              We collect information in the following ways:
            </p>
            <h3 className="text-base font-medium text-zinc-300 mb-2">2.1 Information from Kick OAuth</h3>
            <p className="text-sm text-zinc-400 leading-relaxed mb-2">
              When you authenticate with Kick.com, we receive and store:
            </p>
            <ul className="list-disc list-inside text-sm text-zinc-400 space-y-1">
              <li>Your Kick user ID and username</li>
              <li>Your email address (if provided by Kick)</li>
              <li>Your profile picture URL</li>
              <li>Your channel information</li>
              <li>OAuth access and refresh tokens (encrypted)</li>
            </ul>

            <h3 className="text-base font-medium text-zinc-300 mt-4 mb-2">2.2 Chat & Stream Data</h3>
            <ul className="list-disc list-inside text-sm text-zinc-400 space-y-1">
              <li>Chat messages from your channel (for moderation and logging features)</li>
              <li>Moderation actions and rules you configure</li>
              <li>Giveaway and tournament data you create</li>
            </ul>

            <h3 className="text-base font-medium text-zinc-300 mt-4 mb-2">2.3 Payment Information</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Payment processing is handled by LemonSqueezy and NOWPayments. We do not store your full credit card numbers
              or cryptocurrency wallet addresses. We only store subscription status, plan type, and transaction IDs.
            </p>

            <h3 className="text-base font-medium text-zinc-300 mt-4 mb-2">2.4 Automatically Collected Data</h3>
            <ul className="list-disc list-inside text-sm text-zinc-400 space-y-1">
              <li>IP address and approximate location</li>
              <li>Browser type and version</li>
              <li>Pages visited and time spent</li>
              <li>Referring website</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">3. How We Use Your Information</h2>
            <ul className="list-disc list-inside text-sm text-zinc-400 space-y-1">
              <li>To provide and maintain the Service</li>
              <li>To authenticate your identity and manage your account</li>
              <li>To process payments and manage subscriptions</li>
              <li>To provide chat moderation and bot functionality</li>
              <li>To detect and prevent alt accounts (Anti-Alt feature)</li>
              <li>To generate analytics and insights about your channel</li>
              <li>To improve and optimize the Service</li>
              <li>To send service-related notifications</li>
              <li>To respond to customer support requests</li>
              <li>To comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">4. Data Sharing & Disclosure</h2>
            <p className="text-sm text-zinc-400 leading-relaxed mb-3">
              We do not sell your personal data. We may share information with:
            </p>
            <ul className="list-disc list-inside text-sm text-zinc-400 space-y-1">
              <li><strong className="text-zinc-300">Service Providers:</strong> LemonSqueezy (payments), NOWPayments (crypto payments), OpenAI (AI moderation)</li>
              <li><strong className="text-zinc-300">Kick.com:</strong> API interactions required for the Service to function</li>
              <li><strong className="text-zinc-300">Legal Requirements:</strong> When required by law, court order, or governmental authority</li>
              <li><strong className="text-zinc-300">Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">5. Data Security</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              We implement appropriate technical and organizational measures to protect your personal data, including
              encryption of sensitive data (OAuth tokens, payment information), secure HTTPS connections, and access controls.
              However, no method of transmission over the Internet is 100% secure, and we cannot guarantee absolute security.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">6. Data Retention</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              We retain your personal data for as long as your account is active or as needed to provide the Service. Chat
              logs are retained based on your subscription plan. You may request deletion of your data at any time by
              contacting us. Upon account deletion, we will remove your personal data within 30 days, except where retention
              is required by law.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">7. Your Rights (GDPR)</h2>
            <p className="text-sm text-zinc-400 leading-relaxed mb-3">
              If you are in the European Economic Area (EEA), you have the following rights:
            </p>
            <ul className="list-disc list-inside text-sm text-zinc-400 space-y-1">
              <li><strong className="text-zinc-300">Right of Access:</strong> Request a copy of your personal data</li>
              <li><strong className="text-zinc-300">Right to Rectification:</strong> Request correction of inaccurate data</li>
              <li><strong className="text-zinc-300">Right to Erasure:</strong> Request deletion of your personal data</li>
              <li><strong className="text-zinc-300">Right to Restrict Processing:</strong> Request restriction of data processing</li>
              <li><strong className="text-zinc-300">Right to Data Portability:</strong> Request transfer of your data</li>
              <li><strong className="text-zinc-300">Right to Object:</strong> Object to processing of your personal data</li>
            </ul>
            <p className="text-sm text-zinc-400 leading-relaxed mt-3">
              To exercise these rights, contact us at <span className="text-emerald-400">privacy@kicktools.app</span>.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">8. Cookies</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              We use essential cookies and local storage to maintain your session and preferences. We do not use third-party
              tracking cookies for advertising. By using the Service, you consent to our use of essential cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">9. Children's Privacy</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              The Service is not intended for users under the age of 13. We do not knowingly collect personal data from
              children under 13. If we discover that a child under 13 has provided us with personal data, we will delete
              it immediately.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">10. Changes to This Policy</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              We may update this Privacy Policy from time to time. We will notify you of significant changes by updating
              the "Last updated" date and, where appropriate, by email notification. Continued use of the Service after
              changes constitutes acceptance of the updated policy.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">11. Contact Us</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              For privacy-related questions or to exercise your rights, contact us at{" "}
              <span className="text-emerald-400">privacy@kicktools.app</span>.
            </p>
          </section>
        </div>

        {/* Footer Links */}
        <div className="mt-12 pt-8 border-t border-zinc-800 flex items-center gap-4">
          <button onClick={() => navigate("/terms")} className="text-sm text-zinc-500 hover:text-white transition-colors">
            Terms of Service
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
