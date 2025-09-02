import { Component, type ReactNode } from 'react';
import { QueryErrorResetBoundary } from '@tanstack/react-query';

class ErrorBoundary extends Component<{ onReset: () => void; children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  private handleReset = () => {
    this.setState({ hasError: false });
    this.props.onReset();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" className="p-4 border rounded">
          <p>Une erreur est survenue.</p>
          <button onClick={this.handleReset}>Réessayer</button>
        </div>
      );
    }
    return this.props.children as ReactNode;
  }
}

export function QueryErrorBoundary({ children }: { children: ReactNode }): JSX.Element {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => <ErrorBoundary onReset={reset}>{children}</ErrorBoundary>}
    </QueryErrorResetBoundary>
  );
}

export default QueryErrorBoundary;
