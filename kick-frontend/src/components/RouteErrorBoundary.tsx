import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  /** Human-readable name shown in the error UI (e.g. "Dashboard"). */
  pageName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Per-route ErrorBoundary — wraps individual pages so that a crash in one
 * route doesn't take down the entire application.
 */
export class RouteErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[RouteErrorBoundary${this.props.pageName ? ` — ${this.props.pageName}` : ""}]`, error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 p-8">
          <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-500/10">
            <AlertTriangle className="w-8 h-8 text-amber-400" />
          </div>
          <div className="text-center max-w-md">
            <h3 className="text-lg font-semibold text-white mb-2">
              {this.props.pageName ? `${this.props.pageName} encountered an error` : "This page encountered an error"}
            </h3>
            <p className="text-sm text-zinc-400 mb-1">
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <p className="text-xs text-zinc-500">
              The rest of the app is still working. You can try reloading this page.
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              className="border-zinc-700 text-zinc-300"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try again
            </Button>
            <Button
              variant="outline"
              className="border-zinc-700 text-zinc-300"
              onClick={() => window.location.reload()}
            >
              Reload page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
