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

export function DisclaimerPage() {
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
        <h1 className="text-3xl font-bold mb-2">Disclaimer</h1>
        <p className="text-sm text-zinc-500 mb-8">
          Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
        </p>

        <div className="prose prose-invert prose-zinc max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-white mb-3">General Disclaimer</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              The information and services provided by KickTools ("the Service") are provided on an "as is" and "as available"
              basis. KickTools makes no representations or warranties of any kind, express or implied, regarding the operation
              of the Service, the accuracy, reliability, or completeness of any information, content, or materials provided
              through the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">No Affiliation</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              KickTools is an independent third-party application and is <strong className="text-zinc-300">not affiliated with,
              endorsed by, or officially connected to Kick.com or Kick Streaming Pty Ltd</strong> in any way. The Kick name and
              logo are trademarks of their respective owners. Our use of the Kick API is governed by Kick's API Terms of Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">AI-Powered Features</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              KickTools uses artificial intelligence (AI) for certain features including chat moderation, toxicity detection,
              and alt account detection. While we strive for accuracy, AI systems can produce false positives or false negatives.
              You should review AI-generated moderation actions and not rely solely on automated systems for critical decisions.
              KickTools is not liable for any actions taken based on AI-generated results.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">Stream Content</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              KickTools does not control, monitor, or take responsibility for the content of streams, chat messages, or user
              interactions on Kick.com. Users are solely responsible for their stream content and compliance with Kick.com's
              Terms of Service and Community Guidelines. KickTools provides moderation tools to assist streamers, but ultimate
              responsibility for content moderation lies with the streamer.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">Giveaways & Tournaments</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              KickTools provides tools for organizing giveaways and tournaments. Streamers using these features are solely
              responsible for:
            </p>
            <ul className="list-disc list-inside text-sm text-zinc-400 mt-3 space-y-1">
              <li>Compliance with applicable laws regarding giveaways and contests in their jurisdiction</li>
              <li>Fulfillment of prizes and rewards</li>
              <li>Creating and communicating fair rules to participants</li>
              <li>Ensuring eligibility requirements are met</li>
            </ul>
            <p className="text-sm text-zinc-400 leading-relaxed mt-3">
              KickTools is not responsible for the fulfillment of any prizes, the fairness of any giveaway or tournament, or
              any disputes arising from these activities.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">Payment & Subscription</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Payments are processed by third-party payment processors (LemonSqueezy and NOWPayments). KickTools is not
              responsible for payment processing errors, delays, or issues with these third-party services. Cryptocurrency
              payments are subject to network conditions and exchange rate fluctuations; KickTools is not liable for any
              losses resulting from cryptocurrency price volatility.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">Service Availability</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              While we strive for 99.9% uptime, we do not guarantee uninterrupted access to the Service. The Service may be
              temporarily unavailable due to maintenance, updates, or circumstances beyond our control (including Kick.com API
              outages). We are not liable for any damages resulting from Service downtime.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">External Links</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              The Service may contain links to external websites or services that are not owned or controlled by KickTools.
              We have no control over, and assume no responsibility for, the content, privacy policies, or practices of any
              third-party websites or services. You acknowledge and agree that KickTools shall not be responsible or liable,
              directly or indirectly, for any damage or loss caused by the use of such external content.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">Limitation of Liability</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              To the fullest extent permitted by applicable law, KickTools shall not be liable for any indirect, incidental,
              special, consequential, or punitive damages, or any loss of profits, revenue, data, or use, whether in an
              action in contract, tort, or otherwise, arising out of or in connection with the use of the Service, even if
              KickTools has been advised of the possibility of such damages.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">Changes to This Disclaimer</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              We reserve the right to update or modify this Disclaimer at any time without prior notice. Changes will be
              effective immediately upon posting to the Service. Your continued use of the Service after any changes constitutes
              acceptance of the updated Disclaimer.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">Contact</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              If you have questions about this Disclaimer, contact us at{" "}
              <span className="text-emerald-400">support@kicktools.app</span>.
            </p>
          </section>
        </div>

        {/* Footer Links */}
        <div className="mt-12 pt-8 border-t border-zinc-800 flex items-center gap-4">
          <button onClick={() => navigate("/terms")} className="text-sm text-zinc-500 hover:text-white transition-colors">
            Terms of Service
          </button>
          <span className="text-zinc-700">•</span>
          <button onClick={() => navigate("/privacy")} className="text-sm text-zinc-500 hover:text-white transition-colors">
            Privacy Policy
          </button>
        </div>
      </div>
    </div>
  );
}
