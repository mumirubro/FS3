import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  Globe, CreditCard, Crown, Zap, Gift, Bell,
  Save, CheckCircle2, AlertTriangle, Send
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';

const premiumPlans = [
  { name: 'Basic', price: 10, checks: 100, color: 'from-gray-500 to-gray-600' },
  { name: 'Premium', price: 25, checks: 500, color: 'from-purple-500 to-pink-500', popular: true },
  { name: 'Elite', price: 50, checks: 'Unlimited', color: 'from-yellow-500 to-orange-500' },
];

const gates = [
  { name: 'PayPal CVV', status: 'active', price: '$0.50' },
  { name: 'PayPal $0.1', status: 'active', price: '$0.75' },
  { name: 'Stripe SK', status: 'active', price: '$1.00' },
  { name: 'Stripe Auth', status: 'active', price: '$1.25' },
  { name: 'Shopify', status: 'active', price: '$1.50' },
  { name: 'Stripe Hitter', status: 'active', price: '$0.50' },
];

export default function SettingsTab() {
  const [activeTab, setActiveTab] = useState('proxy');
  const [proxy, setProxy] = useState('');
  const [redeemCode, setRedeemCode] = useState('');
  const [telegramNotifications, setTelegramNotifications] = useState(true);
  const [groupLogs, setGroupLogs] = useState(true);

  // Load saved settings
  useEffect(() => {
    const savedProxy = localStorage.getItem('toji_proxy');
    const savedNotifications = localStorage.getItem('toji_telegram_notifications');
    const savedGroupLogs = localStorage.getItem('toji_group_logs');
    
    if (savedProxy) setProxy(savedProxy);
    if (savedNotifications) setTelegramNotifications(savedNotifications === 'true');
    if (savedGroupLogs) setGroupLogs(savedGroupLogs === 'true');
  }, []);

  const saveProxy = () => {
    localStorage.setItem('toji_proxy', proxy);
    toast.success('Proxy settings saved');
  };

  const saveNotifications = () => {
    localStorage.setItem('toji_telegram_notifications', telegramNotifications.toString());
    localStorage.setItem('toji_group_logs', groupLogs.toString());
    toast.success('Notification settings saved');
  };

  const redeem = () => {
    if (!redeemCode) {
      toast.error('Enter a code');
      return;
    }
    toast.success('Code redeemed successfully!');
    setRedeemCode('');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-black text-white mb-2">
          <span className="bg-gradient-to-r from-gray-400 to-gray-500 bg-clip-text text-transparent">
            Settings
          </span>
        </h2>
        <p className="text-gray-400">Configure your TOJI experience</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6 bg-white/5">
          <TabsTrigger value="proxy" className="data-[state=active]:bg-white/10">
            <Globe className="w-4 h-4 mr-2" />
            Proxy
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-white/10">
            <Bell className="w-4 h-4 mr-2" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="deposit" className="data-[state=active]:bg-white/10">
            <CreditCard className="w-4 h-4 mr-2" />
            Deposit
          </TabsTrigger>
          <TabsTrigger value="premium" className="data-[state=active]:bg-white/10">
            <Crown className="w-4 h-4 mr-2" />
            Premium
          </TabsTrigger>
          <TabsTrigger value="gates" className="data-[state=active]:bg-white/10">
            <Zap className="w-4 h-4 mr-2" />
            Gates
          </TabsTrigger>
          <TabsTrigger value="redeem" className="data-[state=active]:bg-white/10">
            <Gift className="w-4 h-4 mr-2" />
            Redeem
          </TabsTrigger>
        </TabsList>

        {/* Proxy Settings */}
        <TabsContent value="proxy" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Globe className="w-5 h-5 text-cyan-400" />
              Global Proxy Configuration
            </h3>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Default Proxy List (one per line)</label>
                <Textarea
                  placeholder="http://user:pass@host:port&#10;socks5://host:port&#10;host:port"
                  value={proxy}
                  onChange={(e) => setProxy(e.target.value)}
                  className="min-h-[150px] bg-white/5 border-white/10 text-white font-mono text-sm"
                />
              </div>

              <div className="p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                <p className="text-sm text-cyan-400">
                  <Globe className="w-4 h-4 inline mr-2" />
                  These proxies will be available in all checkers. You can enable/disable per-checker.
                </p>
              </div>

              <Button onClick={saveProxy} className="w-full bg-cyan-500 hover:bg-cyan-400">
                <Save className="w-4 h-4 mr-2" />
                Save Proxy Settings
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Notifications Settings */}
        <TabsContent value="notifications" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Bell className="w-5 h-5 text-purple-400" />
              Telegram Notifications
            </h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <p className="text-sm text-white">Private Hit Notifications</p>
                  <p className="text-xs text-gray-500">Send full hit details to your Telegram</p>
                </div>
                <Switch 
                  checked={telegramNotifications} 
                  onCheckedChange={setTelegramNotifications} 
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <p className="text-sm text-white">Group Activity Logs</p>
                  <p className="text-xs text-gray-500">Send activity logs to group (no sensitive data)</p>
                </div>
                <Switch 
                  checked={groupLogs} 
                  onCheckedChange={setGroupLogs} 
                />
              </div>

              <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                <p className="text-sm text-purple-400">
                  <Send className="w-4 h-4 inline mr-2" />
                  Private notifications include full CC/account details. Group logs only show activity (who hit what).
                </p>
              </div>

              <Button onClick={saveNotifications} className="w-full bg-purple-500 hover:bg-purple-400">
                <Save className="w-4 h-4 mr-2" />
                Save Notification Settings
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Deposit */}
        <TabsContent value="deposit" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <CreditCard className="w-5 h-5 text-green-400" />
              Deposit Funds
            </h3>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-white/5 p-4 rounded-lg">
                <p className="text-sm text-gray-400">Current Balance</p>
                <p className="text-2xl font-bold text-white">$0.00</p>
              </div>
              <div className="bg-white/5 p-4 rounded-lg">
                <p className="text-sm text-gray-400">Pending</p>
                <p className="text-2xl font-bold text-yellow-400">$0.00</p>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-sm text-gray-400">Select Amount</p>
              <div className="grid grid-cols-4 gap-3">
                {[10, 25, 50, 100].map(amount => (
                  <Button
                    key={amount}
                    variant="outline"
                    className="border-white/10 hover:bg-white/10"
                  >
                    ${amount}
                  </Button>
                ))}
              </div>
            </div>

            <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                <div>
                  <p className="text-sm text-yellow-400 font-medium">Payment Methods</p>
                  <p className="text-xs text-yellow-400/70 mt-1">
                    We accept Crypto (BTC, ETH, USDT), PayPal, and Credit Cards.
                    Contact @TOJISupport for manual deposits.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Premium */}
        <TabsContent value="premium" className="space-y-6 mt-6">
          <div className="text-center mb-6">
            <h3 className="text-xl font-bold text-white">Upgrade to Premium</h3>
            <p className="text-gray-400">Unlock unlimited checks and exclusive features</p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {premiumPlans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`relative rounded-xl p-6 ${
                  plan.popular
                    ? 'bg-gradient-to-b from-purple-500/20 to-pink-500/20 border-2 border-purple-500/50'
                    : 'bg-white/5 border border-white/10'
                }`}
              >
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500">
                    Most Popular
                  </Badge>
                )}

                <h4 className={`text-xl font-bold mb-2 ${
                  plan.popular ? 'text-purple-400' : 'text-white'
                }`}>
                  {plan.name}
                </h4>
                <p className="text-3xl font-black text-white mb-4">
                  ${plan.price}
                  <span className="text-sm font-normal text-gray-500">/mo</span>
                </p>

                <ul className="space-y-2 mb-6">
                  <li className="flex items-center gap-2 text-sm text-gray-400">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    {plan.checks} Checks
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-400">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Priority Support
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-400">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    All Gates Access
                  </li>
                </ul>

                <Button
                  className={`w-full ${
                    plan.popular
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500'
                      : 'bg-white/10 hover:bg-white/20'
                  }`}
                >
                  Choose {plan.name}
                </Button>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Gates */}
        <TabsContent value="gates" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
              <h3 className="font-semibold text-white">Available Gates</h3>
              <Badge className="bg-green-500/20 text-green-400">
                {gates.filter(g => g.status === 'active').length} Active
              </Badge>
            </div>

            {gates.map((gate) => (
              <div
                key={gate.name}
                className="flex items-center justify-between px-4 py-4 border-b border-white/5 last:border-b-0"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    gate.status === 'active' ? 'bg-green-400' : 'bg-yellow-400'
                  }`} />
                  <span className="text-white">{gate.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">{gate.price}</span>
                  <Badge
                    className={`${
                      gate.status === 'active'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}
                  >
                    {gate.status === 'active' ? 'Active' : 'Maintenance'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Redeem */}
        <TabsContent value="redeem" className="space-y-6 mt-6">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Gift className="w-5 h-5 text-pink-400" />
              Redeem Code
            </h3>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Enter Code</label>
                <Input
                  placeholder="XXXX-XXXX-XXXX"
                  value={redeemCode}
                  onChange={(e) => setRedeemCode(e.target.value.toUpperCase())}
                  className="bg-white/5 border-white/10 text-white font-mono text-center tracking-widest"
                />
              </div>

              <Button onClick={redeem} className="w-full bg-pink-500 hover:bg-pink-400">
                <Gift className="w-4 h-4 mr-2" />
                Redeem
              </Button>

              <p className="text-xs text-gray-500 text-center">
                Codes can be obtained from giveaways, promotions, or by contacting support.
              </p>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
