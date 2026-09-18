// Top-level safety net: catches any render-time exception in the tree
// below it and shows a plain error message instead of an unhandled crash
// silently unmounting the whole app to a blank page. Class component
// because React error boundaries require componentDidCatch/getDerivedState
// from error — there is no hook equivalent.
import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error("Unhandled render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="page">
          <div className="card">
            <h1>Something went wrong</h1>
            <p role="alert" className="alert">
              {this.state.error.message || "An unexpected error occurred."}
            </p>
            <button type="button" className="btn" onClick={() => window.location.assign("/")}>
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
