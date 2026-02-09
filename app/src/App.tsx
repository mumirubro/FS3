import { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
import { SessionProvider, useSession } from './hooks/useSession';
import { ThemeProvider } from './hooks/useTheme';
import RestrictedPage from './sections/RestrictedPage';
import Dashboard from './sections/Dashboard';
import { Loader2 } from 'lucide-react';
import './App.css';

function AppContent() {
  const { sessionToken, isValidating, sessionValid } = useSession();
  const [showDebug, setShowDebug] = useState(false);

  useEffect(() => {
    // Show debug info if needed
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('debug')) {
      setShowDebug(true);
    }
  }, []);

  // Show loading spinner while validating
  if (isValidating) {
    return (
      <div className="min-h-screen bg-[#0a0f1a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-cyan-500 animate-spin" />
          <p className="text-cyan-400 text-lg font-medium animate-pulse">Validating session...</p>
          {showDebug && (
            <div className="mt-4 p-4 bg-white/5 rounded-lg text-xs text-gray-400 font-mono">
              <p>Session Token: {sessionToken ? sessionToken.substring(0, 20) + '...' : 'None'}</p>
              <p>Validating: {isValidating ? 'Yes' : 'No'}</p>
              <p>Session Valid: {sessionValid ? 'Yes' : 'No'}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // If no session token or invalid session, show restricted page
  if (!sessionToken || !sessionValid) {
    return (
      <div className="relative">
        <RestrictedPage />
        {showDebug && (
          <div className="fixed bottom-4 right-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-xs text-red-400 font-mono">
            <p>Debug: No valid session</p>
            <p>Token: {sessionToken ? 'Present' : 'Missing'}</p>
            <p>Valid: {sessionValid ? 'Yes' : 'No'}</p>
          </div>
        )}
      </div>
    );
  }

  // Valid session - show dashboard
  return <Dashboard />;
}

function App() {
  return (
    <ThemeProvider>
      <SessionProvider>
        <div className="min-h-screen bg-[#0a0f1a] text-white font-sans">
          <Toaster 
            position="top-right" 
            theme="dark"
            toastOptions={{
              style: {
                background: '#1a1f2e',
                border: '1px solid rgba(6, 182, 212, 0.3)',
                color: '#fff',
              },
            }}
          />
          <AppContent />
        </div>
      </SessionProvider>
    </ThemeProvider>
  );
}

export default App;
