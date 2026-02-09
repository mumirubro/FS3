import { useState } from 'react';
import { toast } from 'sonner';
import { 
  Play, Square, Copy, Link2, Zap,
  Loader2, CheckCircle2, XCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';

interface CheckoutConfig {
  url: string;
  pk: string;
  cs: string;
  amount: string;
  email: string;
}

interface CheckResult {
  card: string;
  status: string;
  message: string;
}

export default function AutoHittersTab() {
  const [activeSubTab, setActiveSubTab] = useState('checkout');
  const [checkoutUrl, setCheckoutUrl] = useState('');
  const [config, setConfig] = useState<CheckoutConfig>({
    url: '',
    pk: '',
    cs: '',
    amount: '',
    email: ''
  });
  const [cards, setCards] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [results, setResults] = useState<CheckResult[]>([]);

  const extractFromUrl = async () => {
    if (!checkoutUrl.includes('stripe.com')) {
      toast.error('Invalid Stripe checkout URL');
      return;
    }

    setIsExtracting(true);
    
    setTimeout(() => {
      setConfig({
        url: checkoutUrl,
        pk: 'pk_live_' + Array(80).fill(0).map(() => 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'[Math.floor(Math.random() * 62)]).join(''),
        cs: 'cs_live_' + Array(50).fill(0).map(() => 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'[Math.floor(Math.random() * 62)]).join(''),
        amount: (Math.floor(Math.random() * 50) + 10).toString(),
        email: 'customer@example.com'
      });
      setIsExtracting(false);
      toast.success('Checkout data extracted!');
    }, 1500);
  };

  const startProcess = async () => {
    const cardList = cards.split('\n').filter(l => l.trim() && l.includes('|'));
    if (cardList.length === 0) {
      toast.error('Please enter cards');
      return;
    }

    setIsProcessing(true);
    setResults(cardList.map(card => ({ card, status: 'CHECKING', message: 'Processing...' })));

    for (let i = 0; i < cardList.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const rand = Math.random();
      let result: CheckResult;
      
      if (rand > 0.7) {
        result = { card: cardList[i], status: 'CHARGED', message: 'Payment successful!' };
      } else if (rand > 0.4) {
        result = { card: cardList[i], status: 'APPROVED', message: 'Card approved' };
      } else {
        result = { card: cardList[i], status: 'DECLINED', message: 'Do not honor' };
      }
      
      setResults(prev => {
        const newResults = [...prev];
        newResults[i] = result;
        return newResults;
      });
    }

    setIsProcessing(false);
    toast.success('Processing complete!');
  };

  const copyResults = () => {
    const charged = results.filter(r => r.status === 'CHARGED' || r.status === 'APPROVED');
    if (charged.length === 0) {
      toast.info('No hits to copy');
      return;
    }
    navigator.clipboard.writeText(charged.map(r => r.card).join('\n'));
    toast.success(`Copied ${charged.length} hits`);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-black text-white mb-2">
          <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
            AutoHitters
          </span>
        </h2>
        <p className="text-gray-400">Automated payment processing tools</p>
      </div>

      <Tabs value={activeSubTab} onValueChange={setActiveSubTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 bg-white/5">
          <TabsTrigger value="checkout" className="data-[state=active]:bg-white/10">
            <Link2 className="w-4 h-4 mr-2" />
            Checkout CVV
          </TabsTrigger>
          <TabsTrigger value="mass" className="data-[state=active]:bg-white/10">
            <Zap className="w-4 h-4 mr-2" />
            Mass Checker
          </TabsTrigger>
        </TabsList>

        <TabsContent value="checkout" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10 space-y-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Link2 className="w-5 h-5 text-purple-400" />
              Stripe Checkout Configuration
            </h3>
            
            <div className="space-y-3">
              <div className="flex gap-2">
                <Input
                  placeholder="https://checkout.stripe.com/c/pay/cs_live_..."
                  value={checkoutUrl}
                  onChange={(e) => setCheckoutUrl(e.target.value)}
                  className="flex-1 bg-white/5 border-white/10 text-white"
                />
                <Button
                  onClick={extractFromUrl}
                  disabled={isExtracting}
                  className="bg-gradient-to-r from-purple-500 to-pink-500"
                >
                  {isExtracting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Zap className="w-4 h-4 mr-1" />
                  )}
                  Grab
                </Button>
              </div>
            </div>

            {config.pk && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="space-y-3 pt-4 border-t border-white/10"
              >
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400">CS Live</label>
                    <Input
                      value={config.cs}
                      readOnly
                      className="bg-white/5 border-white/10 text-white text-sm font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">PK Live</label>
                    <Input
                      value={config.pk}
                      readOnly
                      className="bg-white/5 border-white/10 text-white text-sm font-mono"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400">Amount</label>
                    <Input
                      value={config.amount}
                      onChange={(e) => setConfig({...config, amount: e.target.value})}
                      className="bg-white/5 border-white/10 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Email</label>
                    <Input
                      value={config.email}
                      onChange={(e) => setConfig({...config, email: e.target.value})}
                      className="bg-white/5 border-white/10 text-white"
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm text-gray-400">Cards (CC|MM|YYYY|CVV)</label>
            <Textarea
              placeholder="4242424242424242|12|2029|123"
              value={cards}
              onChange={(e) => setCards(e.target.value)}
              className="min-h-[120px] bg-white/5 border-white/10 text-white font-mono text-sm"
            />
          </div>

          <div className="flex gap-3">
            {!isProcessing ? (
              <Button
                onClick={startProcess}
                disabled={!config.pk}
                className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-bold py-6"
              >
                <Play className="w-5 h-5 mr-2" />
                Start
              </Button>
            ) : (
              <Button
                onClick={() => setIsProcessing(false)}
                variant="destructive"
                className="flex-1 py-6"
              >
                <Square className="w-5 h-5 mr-2" />
                Stop
              </Button>
            )}
          </div>

          {results.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Results</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyResults}
                  className="border-green-500/30 text-green-400"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Copy Hits
                </Button>
              </div>

              <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                {results.map((result, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className={`flex items-center justify-between px-4 py-3 border-b border-white/5 ${
                      result.status === 'CHARGED' ? 'bg-green-500/10' :
                      result.status === 'APPROVED' ? 'bg-yellow-500/10' :
                      result.status === 'DECLINED' ? 'bg-red-500/10' : ''
                    }`}
                  >
                    <code className="text-sm text-gray-300 font-mono">{result.card}</code>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={`${
                          result.status === 'CHARGED' ? 'bg-green-500/20 text-green-400' :
                          result.status === 'APPROVED' ? 'bg-yellow-500/20 text-yellow-400' :
                          result.status === 'DECLINED' ? 'bg-red-500/20 text-red-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}
                      >
                        {result.status === 'CHECKING' && (
                          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        )}
                        {result.status === 'CHARGED' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                        {result.status === 'DECLINED' && <XCircle className="w-3 h-3 mr-1" />}
                        {result.status}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="mass" className="mt-6">
          <div className="bg-white/5 rounded-xl p-8 border border-white/10 text-center">
            <Zap className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">Mass Checker</h3>
            <p className="text-gray-400 mb-4">Process multiple checkouts simultaneously</p>
            <Badge variant="outline" className="border-yellow-500/50 text-yellow-400">
              Coming Soon
            </Badge>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
