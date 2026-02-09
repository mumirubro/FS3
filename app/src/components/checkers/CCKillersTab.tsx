import { useState } from 'react';
import { toast } from 'sonner';
import { 
  AlertTriangle, Zap, Loader2,
  CheckCircle2, XCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';

interface KillerResult {
  card: string;
  status: string;
  message: string;
}

const killerTypes = [
  { id: 'visa_v1', name: 'Visa Killer V1', attempts: 5 },
  { id: 'visa_v2', name: 'Visa Killer V2', attempts: 3 },
];

export default function CCKillersTab() {
  const [selectedKiller, setSelectedKiller] = useState(0);
  const [card, setCard] = useState('');
  const [isKilling, setIsKilling] = useState(false);
  const [results, setResults] = useState<KillerResult[]>([]);
  const [progress, setProgress] = useState(0);

  const currentKiller = killerTypes[selectedKiller];

  const startKill = async () => {
    if (!card.includes('|')) {
      toast.error('Invalid card format');
      return;
    }

    setIsKilling(true);
    setResults([]);
    setProgress(0);

    for (let i = 0; i < currentKiller.attempts; i++) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setProgress(((i + 1) / currentKiller.attempts) * 100);
      
      const rand = Math.random();
      let result: KillerResult;
      
      if (rand > 0.6) {
        result = { 
          card, 
          status: 'SUCCESS', 
          message: `Kill attempt ${i + 1} successful` 
        };
      } else {
        result = { 
          card, 
          status: 'FAILED', 
          message: `Kill attempt ${i + 1} failed` 
        };
      }
      
      setResults(prev => [...prev, result]);
    }

    setIsKilling(false);
    toast.info('Kill process complete');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-black text-white mb-2">
          <span className="bg-gradient-to-r from-red-400 to-orange-500 bg-clip-text text-transparent">
            CC Killers
          </span>
        </h2>
        <p className="text-gray-400">Advanced card testing tools</p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3"
      >
        <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-red-400 mb-1">Warning</h3>
          <p className="text-sm text-red-400/70">
            This tool sends multiple kill requests to test card limits. 
            Use responsibly. Each attempt costs $0.10 if all succeed.
          </p>
        </div>
      </motion.div>

      <div className="bg-white/5 rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Select Killer</h3>
        <div className="grid grid-cols-2 gap-3">
          {killerTypes.map((killer, index) => (
            <button
              key={killer.id}
              onClick={() => setSelectedKiller(index)}
              className={`p-4 rounded-xl border transition-all ${
                selectedKiller === index
                  ? 'bg-red-500/20 border-red-500/50'
                  : 'bg-white/5 border-white/10 hover:bg-white/10'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <Zap className={`w-5 h-5 ${selectedKiller === index ? 'text-red-400' : 'text-gray-400'}`} />
                <span className={`font-semibold ${selectedKiller === index ? 'text-red-400' : 'text-white'}`}>
                  {killer.name}
                </span>
              </div>
              <p className="text-xs text-gray-500">{killer.attempts} attempts per card</p>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white/5 rounded-xl p-6 border border-white/10 space-y-4">
        <h3 className="text-lg font-semibold text-white">Card Details</h3>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Card (CC|MM|YY|CVV)</label>
          <Input
            placeholder="4242424242424242|12|27|123"
            value={card}
            onChange={(e) => setCard(e.target.value)}
            className="bg-white/5 border-white/10 text-white font-mono"
          />
        </div>

        {isKilling && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-2"
          >
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Progress</span>
              <span className="text-red-400">{Math.round(progress)}%</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-red-500 to-orange-500"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
              />
            </div>
          </motion.div>
        )}

        <Button
          onClick={startKill}
          disabled={isKilling || !card}
          className="w-full bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-400 hover:to-orange-400 text-white font-bold py-6"
        >
          {isKilling ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Zap className="w-5 h-5 mr-2" />
              KILL CARD
            </>
          )}
        </Button>
      </div>

      {results.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-white/5 rounded-xl border border-white/10 overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-white/10">
            <h3 className="font-semibold text-white">Results</h3>
          </div>
          <div className="divide-y divide-white/5">
            {results.map((result, i) => (
              <div
                key={i}
                className="flex items-center justify-between px-4 py-3"
              >
                <span className="text-sm text-gray-400">Attempt {i + 1}</span>
                <div className="flex items-center gap-2">
                  {result.status === 'SUCCESS' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400" />
                  )}
                  <Badge
                    className={`${
                      result.status === 'SUCCESS'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {result.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
