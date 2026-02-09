import { useEffect, useState } from 'react';
import { Shield, Zap, Rocket, Lock, Sparkles, Terminal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

const BOT_USERNAME = 'TOJIchk_bot';
const BOT_URL = `https://t.me/${BOT_USERNAME}`;

// Animated background particles
function Particles() {
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; size: number; delay: number }>>([]);

  useEffect(() => {
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      delay: Math.random() * 5
    }));
    setParticles(newParticles);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full bg-cyan-500/30"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
          }}
          animate={{
            y: [0, -100, 0],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: 8,
            delay: p.delay,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      ))}
    </div>
  );
}

// Glitch text effect
function GlitchText({ text }: { text: string }) {
  return (
    <div className="relative inline-block">
      <span className="relative z-10">{text}</span>
      <span className="absolute top-0 left-0 -z-10 text-red-500/50 animate-pulse translate-x-[2px]">
        {text}
      </span>
      <span className="absolute top-0 left-0 -z-10 text-cyan-500/50 animate-pulse -translate-x-[2px]">
        {text}
      </span>
    </div>
  );
}

export default function RestrictedPage() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0f1a] via-[#0d1321] to-[#0a0f1a] flex items-center justify-center relative overflow-hidden">
      {/* Animated Background */}
      <Particles />
      
      {/* Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.3) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }}
      />

      {/* Glow Effect following mouse */}
      <div 
        className="absolute w-[600px] h-[600px] rounded-full opacity-20 pointer-events-none transition-all duration-300"
        style={{
          background: 'radial-gradient(circle, rgba(6, 182, 212, 0.4) 0%, transparent 70%)',
          left: mousePos.x - 300,
          top: mousePos.y - 300,
        }}
      />

      {/* Main Content */}
      <motion.div 
        className="relative z-10 text-center px-4 max-w-2xl mx-auto"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        {/* Logo */}
        <motion.div 
          className="mb-8"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
        >
          <div className="relative inline-block">
            <div className="w-24 h-24 mx-auto relative">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl rotate-45 animate-pulse" />
              <div className="absolute inset-2 bg-[#0a0f1a] rounded-2xl rotate-45 flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-cyan-400 -rotate-45" />
              </div>
              {/* Orbiting dots */}
              <motion.div
                className="absolute -inset-4"
                animate={{ rotate: 360 }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
              >
                <div className="absolute top-0 left-1/2 w-2 h-2 bg-cyan-400 rounded-full -translate-x-1/2" />
                <div className="absolute bottom-0 left-1/2 w-2 h-2 bg-blue-400 rounded-full -translate-x-1/2" />
                <div className="absolute left-0 top-1/2 w-2 h-2 bg-purple-400 rounded-full -translate-y-1/2" />
                <div className="absolute right-0 top-1/2 w-2 h-2 bg-pink-400 rounded-full -translate-y-1/2" />
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Title */}
        <motion.h1 
          className="text-6xl md:text-7xl font-black mb-4 tracking-tight"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
            <GlitchText text="TOJI" />
          </span>
        </motion.h1>

        <motion.p 
          className="text-cyan-400/80 text-lg mb-8 tracking-widest uppercase"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          Advanced Checker Platform
        </motion.p>

        {/* Main Card */}
        <motion.div 
          className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 mb-8"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 }}
        >
          <div className="flex items-center justify-center gap-3 mb-6">
            <Lock className="w-6 h-6 text-cyan-400" />
            <h2 className="text-xl font-semibold text-white">Authentication Required</h2>
          </div>
          
          <p className="text-gray-400 mb-8 leading-relaxed">
            Please open this app through the Telegram bot to authenticate and access the TOJI platform.
          </p>

          <a href={BOT_URL} target="_blank" rel="noopener noreferrer">
            <Button 
              size="lg"
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold py-6 text-lg rounded-xl transition-all duration-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:scale-[1.02]"
            >
              <svg className="w-6 h-6 mr-2" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 0 0-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
              </svg>
              Open Telegram Bot
            </Button>
          </a>
        </motion.div>

        {/* Features */}
        <motion.div 
          className="grid grid-cols-3 gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          {[
            { icon: Shield, label: 'Secure', color: 'text-green-400' },
            { icon: Zap, label: 'Fast', color: 'text-yellow-400' },
            { icon: Rocket, label: 'Reliable', color: 'text-purple-400' },
          ].map((feature, index) => (
            <motion.div 
              key={feature.label}
              className="flex flex-col items-center gap-2 p-4"
              whileHover={{ scale: 1.05 }}
              transition={{ delay: index * 0.1 }}
            >
              <feature.icon className={`w-8 h-8 ${feature.color}`} />
              <span className="text-sm text-gray-400">{feature.label}</span>
            </motion.div>
          ))}
        </motion.div>

        {/* Footer */}
        <motion.p 
          className="mt-12 text-gray-500 text-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          <Terminal className="w-4 h-4 inline mr-1" />
          Powered by TOJI Technology
        </motion.p>
      </motion.div>
    </div>
  );
}
