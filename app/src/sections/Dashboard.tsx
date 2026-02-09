import { useState, useEffect } from 'react';
import { useSession, useFormattedTime } from '@/hooks/useSession';
import { toast } from 'sonner';
import { 
  User, Settings, CreditCard, Zap, Wrench, LogOut, Clock, 
  Flame, Shield, CheckCircle2, BarChart3, Globe
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { motion, AnimatePresence } from 'framer-motion';
import CheckersTab from '@/components/checkers/CheckersTab';
import ToolsTab from '@/components/checkers/ToolsTab';
import SettingsTab from '@/components/checkers/SettingsTab';
import ProfileTab from '@/components/checkers/ProfileTab';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function SessionTimer() {
  const formattedTime = useFormattedTime();
  const { timeRemaining } = useSession();
  
  const progress = (timeRemaining / (30 * 60)) * 100;
  
  return (
    <div className="px-4 py-3 bg-white/5 border-b border-white/10">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span className="text-sm text-gray-400">Session Time</span>
        </div>
        <span className={`text-sm font-mono font-bold ${
          timeRemaining < 300 ? 'text-red-400 animate-pulse' : 'text-cyan-400'
        }`}>
          {formattedTime}
        </span>
      </div>
      <Progress value={progress} className="h-1.5" />
    </div>
  );
}

function Sidebar({ 
  activeTab, 
  setActiveTab, 
  onLogout 
}: { 
  activeTab: string; 
  setActiveTab: (tab: string) => void;
  onLogout: () => void;
}) {
  const [onlineUsers, setOnlineUsers] = useState(0);
  
  useEffect(() => {
    const fetchOnlineUsers = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/online-users`);
        const data = await response.json();
        setOnlineUsers(data.count);
      } catch (error) {
        console.error('Failed to fetch online users:', error);
      }
    };
    
    fetchOnlineUsers();
    const interval = setInterval(fetchOnlineUsers, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'checkers', label: 'Checkers', icon: CreditCard },
    { id: 'tools', label: 'Tools', icon: Wrench },
  ];

  const bottomItems = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-[#0d1321] border-r border-white/10 flex flex-col h-full">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black text-white tracking-tight">TOJI</h1>
            <p className="text-xs text-cyan-400/70">Advanced Checker</p>
          </div>
        </div>
      </div>

      <SessionTimer />

      <ScrollArea className="flex-1 py-4">
        <nav className="px-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                activeTab === item.id
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
              {activeTab === item.id && (
                <motion.div
                  layoutId="activeIndicator"
                  className="ml-auto w-1.5 h-1.5 bg-cyan-400 rounded-full"
                />
              )}
            </button>
          ))}
        </nav>

        <div className="my-4 mx-4 h-px bg-white/10" />

        <nav className="px-3 space-y-1">
          {bottomItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                activeTab === item.id
                  ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-400 border border-purple-500/30'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
      </ScrollArea>

      <div className="p-4 border-t border-white/10 space-y-3">
        <div className="flex items-center justify-between px-4 py-2 bg-green-500/10 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-sm text-green-400">Online</span>
          </div>
          <span className="text-sm font-bold text-green-400">{onlineUsers}</span>
        </div>
        
        <Button 
          variant="ghost" 
          className="w-full flex items-center gap-2 text-red-400 hover:text-red-300 hover:bg-red-500/10"
          onClick={onLogout}
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </Button>
      </div>
    </div>
  );
}

function StatsBar() {
  const [stats] = useState({
    totalChecked: 0,
    approved: 0,
    live: 0,
    dead: 0
  });

  return (
    <div className="bg-[#0d1321] border-b border-white/10 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-gray-400">Total:</span>
            <span className="text-sm font-bold text-white">{stats.totalChecked}</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
            <span className="text-sm text-gray-400">Approved:</span>
            <span className="text-sm font-bold text-green-400">{stats.approved}</span>
          </div>
          <div className="flex items-center gap-2">
            <Flame className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-gray-400">Live:</span>
            <span className="text-sm font-bold text-yellow-400">{stats.live}</span>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-red-400" />
            <span className="text-sm text-gray-400">Dead:</span>
            <span className="text-sm font-bold text-red-400">{stats.dead}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-cyan-400" />
          <span className="text-xs text-gray-500">Secure Connection</span>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('checkers');
  const { logout } = useSession();

  const handleLogout = () => {
    toast.info('Logging out...');
    logout();
  };

  return (
    <div className="flex h-screen bg-[#0a0f1a]">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        onLogout={handleLogout}
      />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <StatsBar />
        
        <div className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full overflow-auto p-6"
            >
              {activeTab === 'checkers' && <CheckersTab />}
              {activeTab === 'tools' && <ToolsTab />}
              {activeTab === 'profile' && <ProfileTab />}
              {activeTab === 'settings' && <SettingsTab />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
