import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';

// Use environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface User {
  user_id: number;
  username: string;
  first_name: string;
  registered_at: string;
  total_checks: number;
  total_hits: number;
  premium: boolean;
}

interface SessionPayload {
  user_id: number;
  username: string;
  created_at: string;
  expires_at: string;
  active: boolean;
}

interface SessionContextType {
  sessionToken: string | null;
  sessionValid: boolean;
  isValidating: boolean;
  user: User | null;
  timeRemaining: number;
  validateSession: () => Promise<boolean>;
  logout: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

// Decode JWT-like token
function decodeSessionToken(token: string): SessionPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length >= 2) {
      // Add padding if needed
      let payloadBase64 = parts[1];
      while (payloadBase64.length % 4) {
        payloadBase64 += '=';
      }
      const payloadJson = atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(payloadJson) as SessionPayload;
    }
    return null;
  } catch (e) {
    console.error('Failed to decode session token:', e);
    return null;
  }
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [sessionValid, setSessionValid] = useState(false);
  const [isValidating, setIsValidating] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(30 * 60);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Get session from URL or localStorage on mount
  useEffect(() => {
    console.log('SessionProvider: Initializing...');
    
    const urlParams = new URLSearchParams(window.location.search);
    const urlSession = urlParams.get('session');
    const storedSession = localStorage.getItem('toji_session');
    
    console.log('URL Session:', urlSession ? 'Found' : 'Not found');
    console.log('Stored Session:', storedSession ? 'Found' : 'Not found');
    
    const token = urlSession || storedSession;
    
    if (token) {
      console.log('Setting session token:', token.substring(0, 30) + '...');
      setSessionToken(token);
      localStorage.setItem('toji_session', token);
      
      // Remove session from URL if present (clean URL)
      if (urlSession) {
        window.history.replaceState({}, '', window.location.pathname);
      }
    } else {
      console.log('No session found, showing restricted page');
      setIsValidating(false);
    }
  }, []);

  // Validate session (locally from JWT token, or with backend)
  const validateSession = useCallback(async (): Promise<boolean> => {
    if (!sessionToken) {
      console.log('No session token to validate');
      setSessionValid(false);
      return false;
    }

    console.log('Validating session...');
    
    // First, try to decode and validate locally from JWT token
    const payload = decodeSessionToken(sessionToken);
    console.log('Decoded payload:', payload);
    
    if (payload && payload.expires_at) {
      const expiresAt = new Date(payload.expires_at).getTime();
      const now = Date.now();
      
      if (expiresAt > now) {
        console.log('Local validation: Session is valid!');
        setSessionValid(true);
        setUser({
          user_id: payload.user_id,
          username: payload.username || '',
          first_name: '',
          registered_at: '',
          total_checks: 0,
          total_hits: 0,
          premium: false
        });
        setTimeRemaining(Math.floor((expiresAt - now) / 1000));
        
        // Also try to validate with backend for extra security (but don't block if it fails)
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3000);
          
          await fetch(
            `${API_BASE_URL}/api/session/validate?session_token=${sessionToken}`,
            { signal: controller.signal }
          );
          clearTimeout(timeoutId);
        } catch (e) {
          console.warn('Backend validation failed (non-blocking):', e);
        }
        
        return true;
      } else {
        console.log('Local validation: Session expired');
        setSessionValid(false);
        localStorage.removeItem('toji_session');
        toast.error('Session expired. Please create a new session from the bot.');
        return false;
      }
    }
    
    // If local validation failed, try backend
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(
        `${API_BASE_URL}/api/session/validate?session_token=${sessionToken}`,
        { signal: controller.signal }
      );
      clearTimeout(timeoutId);
      
      const data = await response.json();
      console.log('Backend validation response:', data);

      if (data.valid) {
        setSessionValid(true);
        setUser({
          user_id: data.user_id,
          username: data.username || '',
          first_name: '',
          registered_at: '',
          total_checks: 0,
          total_hits: 0,
          premium: false
        });
        
        if (data.expires_at) {
          const expires = new Date(data.expires_at).getTime();
          const now = Date.now();
          const remaining = Math.max(0, Math.floor((expires - now) / 1000));
          setTimeRemaining(remaining);
        }
        
        return true;
      } else {
        setSessionValid(false);
        localStorage.removeItem('toji_session');
        toast.error('Session expired. Please create a new session from the bot.');
        return false;
      }
    } catch (error) {
      console.error('Backend validation failed:', error);
      setSessionValid(false);
      return false;
    }
  }, [sessionToken]);

  // Validate session when token changes
  useEffect(() => {
    if (sessionToken) {
      console.log('Session token changed, validating...');
      validateSession().then((isValid) => {
        console.log('Validation complete, session valid:', isValid);
        setIsValidating(false);
      });
    }
  }, [sessionToken, validateSession]);

  // Countdown timer
  useEffect(() => {
    if (sessionValid && timeRemaining > 0) {
      console.log('Starting countdown timer');
      intervalRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            console.log('Session expired!');
            toast.error('Session expired! Please create a new session from the bot.');
            logout();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [sessionValid, timeRemaining]);

  const logout = useCallback(() => {
    console.log('Logging out...');
    setSessionToken(null);
    setSessionValid(false);
    setUser(null);
    setTimeRemaining(0);
    localStorage.removeItem('toji_session');
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    toast.info('Logged out successfully');
  }, []);

  return (
    <SessionContext.Provider
      value={{
        sessionToken,
        sessionValid,
        isValidating,
        user,
        timeRemaining,
        validateSession,
        logout
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

export function useFormattedTime() {
  const { timeRemaining } = useSession();
  
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  return formatTime(timeRemaining);
}
