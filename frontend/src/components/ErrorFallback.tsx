'use client';

import { ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, WifiOff, Server } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';

interface ErrorFallbackProps {
  error: Error | null;
  resetErrorBoundary: () => void;
  title?: string;
  description?: string;
  showDetails?: boolean;
  onHome?: () => void;
  onRetry?: () => void;
  variant?: 'full' | 'inline' | 'card';
}

export function ErrorFallback({
  error,
  resetErrorBoundary,
  title = 'Something went wrong',
  description = 'An unexpected error occurred. Please try again.',
  showDetails = process.env.NODE_ENV === 'development',
  onHome,
  onRetry,
  variant = 'card',
}: ErrorFallbackProps) {
  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    } else {
      resetErrorBoundary();
    }
  };

  const handleHome = () => {
    if (onHome) {
      onHome();
    } else {
      window.location.href = '/';
    }
  };

  const baseStyles = 'flex flex-col items-center gap-4 p-6 text-center';
  const iconStyles = 'p-3 bg-destructive/10 rounded-full';
  const inlineStyles = 'inline-flex items-center gap-3 p-4 bg-destructive/5 rounded-lg text-sm';

  if (variant === 'inline') {
    return (
      <div className={inlineStyles} role="alert">
        <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0" aria-hidden="true" />
        <div className="flex flex-col gap-2">
          <span className="font-medium">{title}</span>
          <span className="text-muted-foreground">{error?.message || description}</span>
          <Button size="sm" variant="outline" onClick={handleRetry}>
            <RefreshCw className="mr-1 h-3 w-3" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (variant === 'full') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 {iconStyles}">
              <AlertTriangle className="h-10 w-10 text-destructive" />
            </div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {showDetails && error && (
              <details className="text-left">
                <summary className="cursor-pointer font-medium text-sm text-muted-foreground mb-2">
                  Error Details
                </summary>
                <pre className="bg-muted p-3 rounded text-xs overflow-x-auto text-foreground max-h-64">
                  {error.toString()}
                  {error.stack && '\n\n' + error.stack}
                </pre>
              </details>
            )}
            <div className="flex gap-2">
              <Button onClick={handleRetry} className="flex-1">
                <RefreshCw className="mr-2 h-4 w-4" />
                Try Again
              </Button>
              <Button variant="outline" onClick={handleHome} className="flex-1">
                <Home className="mr-2 h-4 w-4" />
                Go Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Card variant - for embedding in layouts
  return (
    <Card className="w-full">
      <CardContent className={baseStyles}>
        <div className={iconStyles}>
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>
        <div className="space-y-2">
          <h3 className="font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
          {showDetails && error && (
            <details className="text-left w-full">
              <summary className="cursor-pointer text-sm text-muted-foreground">
                Show details
              </summary>
              <pre className="bg-muted p-3 rounded text-xs overflow-x-auto text-foreground mt-2 max-h-48">
                {error.toString()}
              </pre>
            </details>
          )}
          <div className="flex gap-2 w-full">
            <Button onClick={handleRetry} className="flex-1">
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
            <Button variant="outline" onClick={handleHome} className="flex-1">
              <Home className="mr-2 h-4 w-4" />
              Home
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Specialized fallbacks for common scenarios
export function NetworkErrorFallback({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorFallback
      error={new Error('Network error')}
      resetErrorBoundary={onRetry || (() => window.location.reload())}
      title="Connection Lost"
      description="Unable to connect to the server. Please check your internet connection and try again."
      variant="card"
    />
  );
}

export function ServerErrorFallback({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorFallback
      error={new Error('Server error')}
      resetErrorBoundary={onRetry || (() => window.location.reload())}
      title="Server Error"
      description="Something went wrong on our end. Our team has been notified."
      variant="card"
    />
  );
}

export function NotFoundFallback({ onHome }: { onHome?: () => void }) {
  return (
    <ErrorFallback
      error={new Error('Not found')}
      resetErrorBoundary={onHome || (() => window.location.href = '/')}
      title="Page Not Found"
      description="The page you're looking for doesn't exist or has been moved."
      variant="full"
    />
  );
}

export function UnauthorizedFallback({ onLogin }: { onLogin?: () => void }) {
  return (
    <ErrorFallback
      error={new Error('Unauthorized')}
      resetErrorBoundary={onLogin || (() => window.location.href = '/login')}
      title="Session Expired"
      description="Please log in again to continue."
      variant="full"
    />
  );
}