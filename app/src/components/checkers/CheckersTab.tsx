import { useState, useRef } from 'react';
import { toast } from 'sonner';
import { 
  Play, Square, Copy, Trash2, Upload, Globe,
  ChevronLeft, ChevronRight, CreditCard, CheckCircle2, 
  Flame, Skull, Zap, Loader2, Link2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { motion } from 'framer-motion';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// All CC Checkers
const ccCheckers = [
  { 
    id: 'paypal-cvv', 
    name: 'PayPal CVV', 
    price: '$0.50', 
    icon: CreditCard, 
    color: 'from-blue-500 to-indigo-500',
    description: 'Check cards with PayPal CVV validation'
  },
  { 
    id: 'paypal-charge', 
    name: 'PayPal $0.1', 
    price: '$0.75', 
    icon: CreditCard, 
    color: 'from-cyan-500 to-blue-500',
    description: 'Charge $0.1 to verify card'
  },
  { 
    id: 'stripe-sk', 
    name: 'Stripe SK', 
    price: '$1.00', 
    icon: Zap, 
    color: 'from-purple-500 to-pink-500',
    description: 'SK key based card checking',
    needsSK: true
  },
  { 
    id: 'stripe-auth', 
    name: 'Stripe Auth', 
    price: '$1.25', 
    icon: Link2, 
    color: 'from-green-500 to-emerald-500',
    description: 'Full Stripe authentication',
    needsURL: true
  },
  { 
    id: 'shopify', 
    name: 'Shopify', 
    price: '$1.50', 
    icon: Globe, 
    color: 'from-orange-500 to-red-500',
    description: 'Shopify checkout automation',
    needsURL: true
  },
  { 
    id: 'stripe-hitter', 
    name: 'Stripe Hitter', 
    price: '$0.50', 
    icon: Zap, 
    color: 'from-yellow-500 to-amber-500',
    description: 'Mass Stripe processing'
  },
];

interface CheckResult {
  card: string;
  status: 'APPROVED' | 'CHARGED' | 'LIVE' | 'DECLINED' | 'ERROR' | 'CHECKING';
  message: string;
  details?: any;
}

export default function CheckersTab() {
  const [selectedChecker, setSelectedChecker] = useState(0);
  const [cards, setCards] = useState('');
  const [skKey, setSkKey] = useState('');
  const [siteUrl, setSiteUrl] = useState('');
  const [proxies, setProxies] = useState('');
  const [useProxy, setUseProxy] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [results, setResults] = useState<CheckResult[]>([]);
  const [stats, setStats] = useState({ approved: 0, charged: 0, live: 0, dead: 0 });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currentChecker = ccCheckers[selectedChecker];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result as string;
        setCards(content);
        toast.success(`Loaded ${content.split('\n').filter(l => l.trim()).length} cards`);
      };
      reader.readAsText(file);
    }
  };

  const parseCards = (text: string): string[] => {
    return text.split('\n')
      .map(line => line.trim())
      .filter(line => line && line.includes('|'));
  };

  const startCheck = async () => {
    const cardList = parseCards(cards);
    if (cardList.length === 0) {
      toast.error('Please enter cards to check');
      return;
    }

    if (currentChecker.needsSK && !skKey) {
      toast.error('Please enter SK key');
      return;
    }

    if (currentChecker.needsURL && !siteUrl) {
      toast.error('Please enter site URL');
      return;
    }

    // Get session token from localStorage
    const sessionToken = localStorage.getItem('toji_session');
    if (!sessionToken) {
      toast.error('Session expired. Please create a new session from the bot.');
      return;
    }

    setIsChecking(true);
    setResults(cardList.map(card => ({ card, status: 'CHECKING', message: 'Pending...' })));
    setStats({ approved: 0, charged: 0, live: 0, dead: 0 });

    try {
      const proxyList = useProxy && proxies ? proxies.split('\n').filter(p => p.trim()) : null;
      
      const requestBody: any = {
        cards: cardList.slice(0, 20),
        proxy_list: proxyList,
        use_proxy: useProxy
      };

      if (currentChecker.needsSK) requestBody.sk_key = skKey;
      if (currentChecker.needsURL) {
        if (currentChecker.id === 'shopify') {
          requestBody.shopify_url = siteUrl;
        } else {
          requestBody.site_url = siteUrl;
        }
      }

      console.log('Sending request to:', `${API_BASE_URL}/api/checker/${currentChecker.id}?session_token=${sessionToken.substring(0, 20)}...`);
      console.log('Request body:', requestBody);

      const response = await fetch(`${API_BASE_URL}/api/checker/${currentChecker.id}?session_token=${sessionToken}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('Response data:', data);

      if (data.success) {
        setResults(data.results);
        setStats({
          approved: data.stats.approved || 0,
          charged: data.stats.charged || 0,
          live: data.stats.live || 0,
          dead: data.stats.declined || data.stats.dead || 0
        });
        
        const hits = (data.stats.approved || 0) + (data.stats.charged || 0) + (data.stats.live || 0);
        toast.success(`Check complete! ${hits} hits found`);
      } else {
        toast.error('Check failed: ' + (data.message || 'Unknown error'));
      }
    } catch (error: any) {
      console.error('Check error:', error);
      toast.error('Check failed: ' + (error.message || 'Network error - make sure backend is running'));
    } finally {
      setIsChecking(false);
    }
  };

  const stopCheck = () => {
    setIsChecking(false);
    toast.info('Check stopped');
  };

  const clearAll = () => {
    setCards('');
    setResults([]);
    setStats({ approved: 0, charged: 0, live: 0, dead: 0 });
    toast.info('Cleared');
  };

  const copyHits = () => {
    const hits = results.filter(r => ['APPROVED', 'CHARGED', 'LIVE'].includes(r.status));
    if (hits.length === 0) {
      toast.info('No hits to copy');
      return;
    }
    const text = hits.map(r => r.card).join('\n');
    navigator.clipboard.writeText(text);
    toast.success(`Copied ${hits.length} hits`);
  };

  const copyAll = () => {
    if (results.length === 0) return;
    const text = results.map(r => `${r.card} | ${r.status} | ${r.message}`).join('\n');
    navigator.clipboard.writeText(text);
    toast.success('Copied all results');
  };

  const navigateChecker = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      setSelectedChecker(prev => (prev === 0 ? ccCheckers.length - 1 : prev - 1));
    } else {
      setSelectedChecker(prev => (prev === ccCheckers.length - 1 ? 0 : prev + 1));
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-black text-white mb-2">
          <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            CC Checkers
          </span>
        </h2>
        <p className="text-gray-400">Advanced credit card checking gates</p>
      </div>

      {/* Checker Selector */}
      <div className="flex items-center justify-center gap-4">
        <Button
          variant="outline"
          size="icon"
          onClick={() => navigateChecker('prev')}
          className="border-white/10 hover:bg-white/5"
        >
          <ChevronLeft className="w-5 h-5" />
        </Button>
        
        <motion.div
          key={currentChecker.id}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`px-6 py-4 rounded-2xl bg-gradient-to-r ${currentChecker.color} flex items-center gap-4 min-w-[300px]`}
        >
          <currentChecker.icon className="w-8 h-8 text-white" />
          <div className="text-left">
            <p className="font-bold text-white text-lg">{currentChecker.name}</p>
            <p className="text-xs text-white/70">{currentChecker.price} per check</p>
            <p className="text-xs text-white/50 mt-1">{currentChecker.description}</p>
          </div>
        </motion.div>
        
        <Button
          variant="outline"
          size="icon"
          onClick={() => navigateChecker('next')}
          className="border-white/10 hover:bg-white/5"
        >
          <ChevronRight className="w-5 h-5" />
        </Button>
      </div>

      {/* SK Key Input */}
      {currentChecker.needsSK && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="space-y-2"
        >
          <label className="text-sm text-gray-400">SK Key</label>
          <Input
            type="password"
            placeholder="sk_live_..."
            value={skKey}
            onChange={(e) => setSkKey(e.target.value)}
            className="bg-white/5 border-white/10 text-white placeholder:text-gray-600"
          />
        </motion.div>
      )}

      {/* Site URL Input */}
      {currentChecker.needsURL && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="space-y-2"
        >
          <label className="text-sm text-gray-400">
            {currentChecker.id === 'shopify' ? 'Shopify Store URL' : 'WooCommerce Site URL'}
          </label>
          <Input
            placeholder={currentChecker.id === 'shopify' ? 'https://store.myshopify.com' : 'https://example.com'}
            value={siteUrl}
            onChange={(e) => setSiteUrl(e.target.value)}
            className="bg-white/5 border-white/10 text-white placeholder:text-gray-600"
          />
        </motion.div>
      )}

      {/* Proxy Configuration */}
      <div className="bg-white/5 rounded-xl p-4 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-cyan-400" />
            <span className="text-white font-medium">Proxy Configuration</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Use Proxy</span>
            <Switch checked={useProxy} onCheckedChange={setUseProxy} />
          </div>
        </div>
        
        {useProxy && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
          >
            <Textarea
              placeholder="http://user:pass@host:port&#10;socks5://host:port&#10;host:port"
              value={proxies}
              onChange={(e) => setProxies(e.target.value)}
              className="min-h-[80px] bg-white/5 border-white/10 text-white placeholder:text-gray-600 font-mono text-sm"
            />
            <p className="text-xs text-gray-500 mt-2">
              Supports HTTP, SOCKS4, SOCKS5. One proxy per line.
            </p>
          </motion.div>
        )}
      </div>

      {/* Cards Input */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm text-gray-400">Cards (CC|MM|YYYY|CVV)</label>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="text-gray-400 hover:text-white"
            >
              <Upload className="w-4 h-4 mr-1" />
              Import
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt"
              onChange={handleFileUpload}
              className="hidden"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAll}
              className="text-red-400 hover:text-red-300"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Clear
            </Button>
          </div>
        </div>
        <Textarea
          placeholder="4242424242424242|12|2029|123&#10;4111111111111111|06|2028|999"
          value={cards}
          onChange={(e) => setCards(e.target.value)}
          className="min-h-[150px] bg-white/5 border-white/10 text-white placeholder:text-gray-600 font-mono text-sm"
        />
        <p className="text-xs text-gray-500">
          {parseCards(cards).length} cards loaded
        </p>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-3">
        {!isChecking ? (
          <Button
            onClick={startCheck}
            className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-bold py-6"
          >
            <Play className="w-5 h-5 mr-2" />
            Start Check
          </Button>
        ) : (
          <Button
            onClick={stopCheck}
            variant="destructive"
            className="flex-1 py-6"
          >
            <Square className="w-5 h-5 mr-2" />
            Stop
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center">
          <CheckCircle2 className="w-6 h-6 text-green-400 mx-auto mb-2" />
          <p className="text-2xl font-bold text-green-400">{stats.approved}</p>
          <p className="text-xs text-green-400/70">Approved</p>
        </div>
        <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-4 text-center">
          <Zap className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
          <p className="text-2xl font-bold text-cyan-400">{stats.charged}</p>
          <p className="text-xs text-cyan-400/70">Charged</p>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 text-center">
          <Flame className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
          <p className="text-2xl font-bold text-yellow-400">{stats.live}</p>
          <p className="text-xs text-yellow-400/70">Live</p>
        </div>
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-center">
          <Skull className="w-6 h-6 text-red-400 mx-auto mb-2" />
          <p className="text-2xl font-bold text-red-400">{stats.dead}</p>
          <p className="text-xs text-red-400/70">Dead</p>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Results</h3>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={copyHits}
                className="border-green-500/30 text-green-400 hover:bg-green-500/10"
              >
                <Copy className="w-4 h-4 mr-1" />
                Copy Hits
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={copyAll}
                className="border-white/10"
              >
                <Copy className="w-4 h-4 mr-1" />
                Copy All
              </Button>
            </div>
          </div>

          <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <div className="max-h-[300px] overflow-auto">
              {results.map((result, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className={`flex items-center justify-between px-4 py-3 border-b border-white/5 last:border-b-0 ${
                    result.status === 'APPROVED' || result.status === 'CHARGED' ? 'bg-green-500/5' :
                    result.status === 'LIVE' ? 'bg-yellow-500/5' :
                    result.status === 'DECLINED' ? 'bg-red-500/5' :
                    result.status === 'CHECKING' ? 'bg-blue-500/5' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-gray-500 text-sm w-8">#{index + 1}</span>
                    <code className="text-sm text-gray-300 font-mono">{result.card}</code>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className={`${
                        result.status === 'APPROVED' || result.status === 'CHARGED' ? 'border-green-500/50 text-green-400 bg-green-500/10' :
                        result.status === 'LIVE' ? 'border-yellow-500/50 text-yellow-400 bg-yellow-500/10' :
                        result.status === 'DECLINED' ? 'border-red-500/50 text-red-400 bg-red-500/10' :
                        result.status === 'CHECKING' ? 'border-blue-500/50 text-blue-400 bg-blue-500/10' :
                        'border-gray-500/50 text-gray-400'
                      }`}
                    >
                      {result.status === 'CHECKING' && (
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      )}
                      {result.status}
                    </Badge>
                    <span className="text-xs text-gray-500 max-w-[200px] truncate">
                      {result.message}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
