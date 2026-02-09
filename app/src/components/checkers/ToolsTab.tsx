import { useState } from 'react';
import { toast } from 'sonner';
import { 
  Key, Search, Gamepad2, Mail, Play, Loader2, Copy,
  CheckCircle2, XCircle, ExternalLink, Globe, Check
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SKResult {
  key: string;
  valid: boolean;
  message: string;
  type?: string;
  balance?: number;
  currency?: string;
}

interface AccountResult {
  combo: string;
  status: string;
  message: string;
  details?: any;
}

interface ProxyResult {
  proxy: string;
  working: boolean;
  response_time?: number;
}

export default function ToolsTab() {
  const [activeTool, setActiveTool] = useState('sk');
  
  // SK Checker state
  const [skKeys, setSkKeys] = useState('');
  const [skResults, setSkResults] = useState<SKResult[]>([]);
  const [isCheckingSK, setIsCheckingSK] = useState(false);
  
  // Account checker state
  const [combos, setCombos] = useState('');
  const [accountResults, setAccountResults] = useState<AccountResult[]>([]);
  const [isCheckingAccounts, setIsCheckingAccounts] = useState(false);
  
  // Proxy checker state
  const [proxyList, setProxyList] = useState('');
  const [proxyResults, setProxyResults] = useState<ProxyResult[]>([]);
  const [isCheckingProxies, setIsCheckingProxies] = useState(false);

  const getSessionToken = () => {
    return localStorage.getItem('toji_session');
  };

  const checkSKKeys = async () => {
    const keys = skKeys.split('\n').filter(k => k.trim().startsWith('sk_'));
    if (keys.length === 0) {
      toast.error('Please enter valid SK keys');
      return;
    }

    const sessionToken = getSessionToken();
    if (!sessionToken) {
      toast.error('Session expired. Please create a new session from the bot.');
      return;
    }

    setIsCheckingSK(true);
    setSkResults(keys.map(k => ({ key: k.trim(), valid: false, message: 'Checking...' })));

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/sk-checker?session_token=${sessionToken}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sk_keys: keys.slice(0, 50) })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setSkResults(data.results);
        toast.success(`SK check complete! ${data.stats.valid} valid keys`);
      } else {
        toast.error('SK check failed');
      }
    } catch (error: any) {
      console.error('SK check error:', error);
      toast.error('SK check failed: ' + (error.message || 'Network error'));
    } finally {
      setIsCheckingSK(false);
    }
  };

  const checkAccounts = async (type: string) => {
    const comboList = combos.split('\n').filter(c => c.trim().includes(':'));
    if (comboList.length === 0) {
      toast.error('Please enter valid combos (email:password)');
      return;
    }

    const sessionToken = getSessionToken();
    if (!sessionToken) {
      toast.error('Session expired. Please create a new session from the bot.');
      return;
    }

    setIsCheckingAccounts(true);
    setAccountResults(comboList.map(c => ({ combo: c.trim(), status: 'CHECKING', message: 'Checking...' })));

    try {
      const response = await fetch(`${API_BASE_URL}/api/checker/${type}?session_token=${sessionToken}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ combos: comboList.slice(0, 20) })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setAccountResults(data.results);
        toast.success(`${type} check complete! ${data.stats.hits} hits`);
      } else {
        toast.error('Check failed');
      }
    } catch (error: any) {
      console.error('Account check error:', error);
      toast.error('Check failed: ' + (error.message || 'Network error'));
    } finally {
      setIsCheckingAccounts(false);
    }
  };

  const checkProxies = async () => {
    const proxies = proxyList.split('\n').filter(p => p.trim());
    if (proxies.length === 0) {
      toast.error('Please enter proxies to test');
      return;
    }

    const sessionToken = getSessionToken();
    if (!sessionToken) {
      toast.error('Session expired. Please create a new session from the bot.');
      return;
    }

    setIsCheckingProxies(true);
    setProxyResults(proxies.map(p => ({ proxy: p.trim(), working: false })));

    try {
      const response = await fetch(`${API_BASE_URL}/api/tools/proxy-test?session_token=${sessionToken}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proxies: proxies.slice(0, 50) })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setProxyResults(data.results);
        toast.success(`Proxy test complete! ${data.stats.working} working`);
      } else {
        toast.error('Proxy test failed');
      }
    } catch (error: any) {
      console.error('Proxy test error:', error);
      toast.error('Proxy test failed: ' + (error.message || 'Network error'));
    } finally {
      setIsCheckingProxies(false);
    }
  };

  const copyValidSK = () => {
    const valid = skResults.filter(r => r.valid);
    if (valid.length === 0) {
      toast.info('No valid keys');
      return;
    }
    navigator.clipboard.writeText(valid.map(r => r.key).join('\n'));
    toast.success(`Copied ${valid.length} valid keys`);
  };

  const copyHits = () => {
    const hits = accountResults.filter(r => r.status === 'HIT');
    if (hits.length === 0) {
      toast.info('No hits');
      return;
    }
    navigator.clipboard.writeText(hits.map(r => r.combo).join('\n'));
    toast.success(`Copied ${hits.length} hits`);
  };

  const copyWorkingProxies = () => {
    const working = proxyResults.filter(r => r.working);
    if (working.length === 0) {
      toast.info('No working proxies');
      return;
    }
    navigator.clipboard.writeText(working.map(r => r.proxy).join('\n'));
    toast.success(`Copied ${working.length} working proxies`);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-black text-white mb-2">
          <span className="bg-gradient-to-r from-orange-400 to-yellow-500 bg-clip-text text-transparent">
            Tools
          </span>
        </h2>
        <p className="text-gray-400">Account checkers and utilities</p>
      </div>

      <Tabs value={activeTool} onValueChange={setActiveTool} className="w-full">
        <TabsList className="grid w-full grid-cols-5 bg-white/5">
          <TabsTrigger value="sk" className="data-[state=active]:bg-white/10">
            <Key className="w-4 h-4 mr-2" />
            SK Checker
          </TabsTrigger>
          <TabsTrigger value="hotmail" className="data-[state=active]:bg-white/10">
            <Mail className="w-4 h-4 mr-2" />
            Hotmail
          </TabsTrigger>
          <TabsTrigger value="steam" className="data-[state=active]:bg-white/10">
            <Gamepad2 className="w-4 h-4 mr-2" />
            Steam
          </TabsTrigger>
          <TabsTrigger value="crunchyroll" className="data-[state=active]:bg-white/10">
            <ExternalLink className="w-4 h-4 mr-2" />
            Crunchyroll
          </TabsTrigger>
          <TabsTrigger value="proxy" className="data-[state=active]:bg-white/10">
            <Globe className="w-4 h-4 mr-2" />
            Proxy Test
          </TabsTrigger>
        </TabsList>

        {/* SK Checker */}
        <TabsContent value="sk" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Key className="w-5 h-5 text-orange-400" />
                Stripe Key Checker
              </h3>
              <Badge className="bg-green-500/20 text-green-400">Free</Badge>
            </div>

            <div className="space-y-4">
              <Textarea
                placeholder="sk_live_...&#10;sk_test_..."
                value={skKeys}
                onChange={(e) => setSkKeys(e.target.value)}
                className="min-h-[150px] bg-white/5 border-white/10 text-white font-mono text-sm"
              />

              <Button
                onClick={checkSKKeys}
                disabled={isCheckingSK}
                className="w-full bg-gradient-to-r from-orange-500 to-yellow-500"
              >
                {isCheckingSK ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Search className="w-4 h-4 mr-2" />
                )}
                Check Keys
              </Button>
            </div>
          </div>

          {skResults.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Results</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyValidSK}
                  className="border-green-500/30 text-green-400"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Copy Valid
                </Button>
              </div>

              <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                {skResults.map((result, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center justify-between px-4 py-3 border-b border-white/5 last:border-b-0"
                  >
                    <code className="text-sm text-gray-300 font-mono truncate max-w-[300px]">
                      {result.key.substring(0, 25)}...
                    </code>
                    <div className="flex items-center gap-3">
                      {result.valid && (
                        <span className="text-xs text-gray-500">
                          ${result.balance?.toFixed(2)} {result.currency}
                        </span>
                      )}
                      <Badge
                        className={`${
                          result.valid
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}
                      >
                        {result.valid ? (
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                        ) : (
                          <XCircle className="w-3 h-3 mr-1" />
                        )}
                        {result.valid ? 'VALID' : 'INVALID'}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Hotmail Checker */}
        <TabsContent value="hotmail" className="space-y-6 mt-6">
          <AccountChecker
            type="hotmail"
            icon={Mail}
            combos={combos}
            setCombos={setCombos}
            results={accountResults}
            isChecking={isCheckingAccounts}
            onCheck={() => checkAccounts('hotmail')}
            onCopy={copyHits}
          />
        </TabsContent>

        {/* Steam Checker */}
        <TabsContent value="steam" className="space-y-6 mt-6">
          <AccountChecker
            type="steam"
            icon={Gamepad2}
            combos={combos}
            setCombos={setCombos}
            results={accountResults}
            isChecking={isCheckingAccounts}
            onCheck={() => checkAccounts('steam')}
            onCopy={copyHits}
          />
        </TabsContent>

        {/* Crunchyroll Checker */}
        <TabsContent value="crunchyroll" className="space-y-6 mt-6">
          <AccountChecker
            type="crunchyroll"
            icon={ExternalLink}
            combos={combos}
            setCombos={setCombos}
            results={accountResults}
            isChecking={isCheckingAccounts}
            onCheck={() => checkAccounts('crunchyroll')}
            onCopy={copyHits}
          />
        </TabsContent>

        {/* Proxy Test */}
        <TabsContent value="proxy" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Globe className="w-5 h-5 text-cyan-400" />
                Proxy Tester
              </h3>
              <Badge className="bg-green-500/20 text-green-400">Free</Badge>
            </div>

            <div className="space-y-4">
              <Textarea
                placeholder="http://user:pass@host:port&#10;socks5://host:port&#10;host:port"
                value={proxyList}
                onChange={(e) => setProxyList(e.target.value)}
                className="min-h-[150px] bg-white/5 border-white/10 text-white font-mono text-sm"
              />

              <Button
                onClick={checkProxies}
                disabled={isCheckingProxies}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500"
              >
                {isCheckingProxies ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Check className="w-4 h-4 mr-2" />
                )}
                Test Proxies
              </Button>
            </div>
          </div>

          {proxyResults.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Results</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyWorkingProxies}
                  className="border-green-500/30 text-green-400"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Copy Working
                </Button>
              </div>

              <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                {proxyResults.map((result, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center justify-between px-4 py-3 border-b border-white/5 last:border-b-0"
                  >
                    <code className="text-sm text-gray-300 font-mono">{result.proxy}</code>
                    <div className="flex items-center gap-2">
                      {result.working && result.response_time && (
                        <span className="text-xs text-gray-500">{result.response_time}s</span>
                      )}
                      <Badge
                        className={`${
                          result.working
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}
                      >
                        {result.working ? 'WORKING' : 'FAILED'}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Account Checker Component
function AccountChecker({ 
  type, 
  icon: Icon, 
  combos, 
  setCombos, 
  results, 
  isChecking, 
  onCheck, 
  onCopy 
}: {
  type: string;
  icon: any;
  combos: string;
  setCombos: (v: string) => void;
  results: AccountResult[];
  isChecking: boolean;
  onCheck: () => void;
  onCopy: () => void;
}) {
  return (
    <div className="space-y-6">
      <div className="bg-white/5 rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
          <Icon className="w-5 h-5 text-orange-400" />
          {type.charAt(0).toUpperCase() + type.slice(1)} Account Checker
        </h3>

        <div className="space-y-4">
          <Textarea
            placeholder={`email:password\nemail:password`}
            value={combos}
            onChange={(e) => setCombos(e.target.value)}
            className="min-h-[150px] bg-white/5 border-white/10 text-white font-mono text-sm"
          />

          <Button
            onClick={onCheck}
            disabled={isChecking}
            className="w-full bg-gradient-to-r from-orange-500 to-yellow-500"
          >
            {isChecking ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Play className="w-4 h-4 mr-2" />
            )}
            Check Accounts
          </Button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Results</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={onCopy}
              className="border-green-500/30 text-green-400"
            >
              <Copy className="w-4 h-4 mr-1" />
              Copy Hits
            </Button>
          </div>

          <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            {results.map((result, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={`flex items-center justify-between px-4 py-3 border-b border-white/5 ${
                  result.status === 'HIT' ? 'bg-green-500/10' :
                  result.status === 'LIVE' ? 'bg-yellow-500/10' :
                  result.status === 'DEAD' ? 'bg-red-500/10' : ''
                }`}
              >
                <code className="text-sm text-gray-300 font-mono">{result.combo}</code>
                <div className="flex items-center gap-2">
                  {result.status === 'HIT' && result.details && (
                    <span className="text-xs text-gray-500">
                      {Object.keys(result.details).slice(0, 2).join(', ')}
                    </span>
                  )}
                  <Badge
                    className={`${
                      result.status === 'HIT' ? 'bg-green-500/20 text-green-400' :
                      result.status === 'LIVE' ? 'bg-yellow-500/20 text-yellow-400' :
                      result.status === 'DEAD' ? 'bg-red-500/20 text-red-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}
                  >
                    {result.status}
                  </Badge>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
