import { useState, useEffect } from 'react';
import { 
  User, Trophy, Users, BarChart3, Crown, Zap, CheckCircle2,
  Flame, Skull, CreditCard, Calendar, Hash
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import { useSession } from '@/hooks/useSession';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface LeaderboardUser {
  user_id: number;
  username: string;
  first_name: string;
  total_hits: number;
  total_checks: number;
}

interface OnlineUser {
  user_id: number;
  username: string;
  since: string;
}

export default function ProfileTab() {
  const { user, sessionToken } = useSession();
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([]);
  const [stats, setStats] = useState({
    totalChecks: 0,
    totalHits: 0,
    successRate: 0
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const lbResponse = await fetch(`${API_BASE_URL}/api/leaderboard`);
        const lbData = await lbResponse.json();
        setLeaderboard(lbData.leaderboard || []);

        const onlineResponse = await fetch(`${API_BASE_URL}/api/online-users`);
        const onlineData = await onlineResponse.json();
        setOnlineUsers(onlineData.online_users || []);

        if (sessionToken) {
          const profileResponse = await fetch(`${API_BASE_URL}/api/user/profile?session_token=${sessionToken}`);
          const profileData = await profileResponse.json();
          const totalChecks = profileData.total_checks || 0;
          const totalHits = profileData.total_hits || 0;
          setStats({
            totalChecks,
            totalHits,
            successRate: totalChecks > 0 
              ? parseFloat(((totalHits / totalChecks) * 100).toFixed(1))
              : 0
          });
        }
      } catch (error) {
        console.error('Failed to fetch data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [sessionToken]);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-black text-white mb-2">
          <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
            Profile
          </span>
        </h2>
        <p className="text-gray-400">Your TOJI statistics and leaderboard</p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl p-6 border border-purple-500/30"
      >
        <div className="flex items-center gap-6">
          <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center">
            <User className="w-10 h-10 text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-2xl font-bold text-white">{user?.first_name || 'User'}</h3>
              <Badge className="bg-purple-500/20 text-purple-400">
                <Crown className="w-3 h-3 mr-1" />
                {user?.premium ? 'Premium' : 'Free'}
              </Badge>
            </div>
            <p className="text-gray-400">@{user?.username || 'unknown'}</p>
            <p className="text-sm text-gray-500 mt-1">
              <Hash className="w-3 h-3 inline mr-1" />
              ID: {user?.user_id}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-white/5 rounded-xl p-4 text-center">
            <BarChart3 className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats.totalChecks}</p>
            <p className="text-xs text-gray-500">Total Checks</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4 text-center">
            <CheckCircle2 className="w-6 h-6 text-green-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats.totalHits}</p>
            <p className="text-xs text-gray-500">Total Hits</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4 text-center">
            <Zap className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats.successRate}%</p>
            <p className="text-xs text-gray-500">Success Rate</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4 text-center">
            <Trophy className="w-6 h-6 text-purple-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">#{leaderboard.findIndex(u => u.user_id === user?.user_id) + 1 || '-'}</p>
            <p className="text-xs text-gray-500">Rank</p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white/5 rounded-xl border border-white/10 overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-400" />
              Top Carders
            </h3>
            <Badge className="bg-yellow-500/20 text-yellow-400">
              {leaderboard.length} Users
            </Badge>
          </div>

          <div className="max-h-[300px] overflow-auto">
            {leaderboard.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Trophy className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No data available</p>
              </div>
            ) : (
              leaderboard.slice(0, 10).map((u, index) => (
                <div
                  key={u.user_id}
                  className={`flex items-center justify-between px-4 py-3 border-b border-white/5 ${
                    u.user_id === user?.user_id ? 'bg-purple-500/10' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      index === 0 ? 'bg-yellow-500 text-black' :
                      index === 1 ? 'bg-gray-400 text-black' :
                      index === 2 ? 'bg-orange-600 text-white' :
                      'bg-white/10 text-gray-400'
                    }`}>
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-sm text-white">{u.first_name || u.username}</p>
                      <p className="text-xs text-gray-500">@{u.username}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-green-400">{u.total_hits} hits</p>
                    <p className="text-xs text-gray-500">{u.total_checks} checks</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/5 rounded-xl border border-white/10 overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-green-400" />
              Online Now
            </h3>
            <Badge className="bg-green-500/20 text-green-400">
              {onlineUsers.length} Online
            </Badge>
          </div>

          <div className="max-h-[300px] overflow-auto">
            {onlineUsers.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No users online</p>
              </div>
            ) : (
              onlineUsers.map((u) => (
                <div
                  key={u.user_id}
                  className="flex items-center justify-between px-4 py-3 border-b border-white/5"
                >
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-xs font-bold text-white">
                          {(u.username || 'U').charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-[#0a0f1a]" />
                    </div>
                    <div>
                      <p className="text-sm text-white">@{u.username}</p>
                      <p className="text-xs text-gray-500">
                        <Calendar className="w-3 h-3 inline mr-1" />
                        {new Date(u.since).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white/5 rounded-xl border border-white/10 p-6"
      >
        <h3 className="font-semibold text-white flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-cyan-400" />
          Recent Activity
        </h3>

        <div className="grid grid-cols-4 gap-4">
          <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
            <CreditCard className="w-8 h-8 text-cyan-400" />
            <div>
              <p className="text-lg font-bold text-white">0</p>
              <p className="text-xs text-gray-500">Cards Checked</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
            <CheckCircle2 className="w-8 h-8 text-green-400" />
            <div>
              <p className="text-lg font-bold text-white">0</p>
              <p className="text-xs text-gray-500">Approved</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
            <Flame className="w-8 h-8 text-yellow-400" />
            <div>
              <p className="text-lg font-bold text-white">0</p>
              <p className="text-xs text-gray-500">Live</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-white/5 rounded-lg">
            <Skull className="w-8 h-8 text-red-400" />
            <div>
              <p className="text-lg font-bold text-white">0</p>
              <p className="text-xs text-gray-500">Dead</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
