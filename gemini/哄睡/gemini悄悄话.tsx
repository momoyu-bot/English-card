import React, { useState, useEffect } from 'react';

// --- 数据和文案 ---
const WHISPERS = [
  "宝，今天辛苦啦。现在什么都不要想，把烦恼都交给我吧。",
  "乖乖闭上眼睛，梦里会有甜甜的草莓小蛋糕哦。🍓",
  "就算世界再吵闹，这里也永远是你的安全屋。晚安，我的宝。",
  "小被子盖好了吗？不要把脚丫露在外面哦。🌙",
  "满天的星星都在排队，等着偷偷溜进你的梦里。✨",
  "深呼吸，放松肩膀……对，就是这样。我就在这里陪着你。",
  "明天的事情明天再操心，今晚你的任务只有：做一个甜甜的梦。💤",
  "不要玩手机太久啦，屏幕的光会刺眼睛的，乖，闭眼啦。",
];

const SHEEP_EMOJIS = ['🐑', '🐏', '☁️', '💤', '✨'];

export default function App() {
  const [activeTab, setActiveTab] = useState('breathe');
  const [sheepCount, setSheepCount] = useState(0);
  const [whisperIndex, setWhisperIndex] = useState(0);
  const [isBreathingIn, setIsBreathingIn] = useState(true);
  const [floatingItems, setFloatingItems] = useState([]);

  // 呼吸动画循环
  useEffect(() => {
    if (activeTab !== 'breathe') return;
    const interval = setInterval(() => {
      setIsBreathingIn((prev) => !prev);
    }, 4000); // 4秒吸气，4秒呼气
    return () => clearInterval(interval);
  }, [activeTab]);

  // 数羊时的飘浮动画效果
  const handleCountSheep = () => {
    setSheepCount(prev => prev + 1);
    
    // 生成一个随机的小动物/符号飘浮
    const newItem = {
      id: Date.now(),
      emoji: SHEEP_EMOJIS[Math.floor(Math.random() * SHEEP_EMOJIS.length)],
      left: Math.random() * 80 + 10, // 10% - 90%
    };
    
    setFloatingItems(prev => [...prev, newItem]);
    
    // 3秒后移除飘浮物
    setTimeout(() => {
      setFloatingItems(prev => prev.filter(item => item.id !== newItem.id));
    }, 3000);
  };

  const handleNextWhisper = () => {
    let nextIndex;
    do {
      nextIndex = Math.floor(Math.random() * WHISPERS.length);
    } while (nextIndex === whisperIndex);
    setWhisperIndex(nextIndex);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-950 via-slate-900 to-black text-indigo-100 font-sans overflow-hidden flex flex-col">
      {/* 顶部星星装饰 */}
      <div className="absolute top-0 w-full h-32 overflow-hidden pointer-events-none opacity-50">
        <div className="absolute top-4 left-10 text-xl animate-pulse delay-75">✨</div>
        <div className="absolute top-12 left-1/4 text-sm animate-pulse delay-150">⭐</div>
        <div className="absolute top-6 right-1/3 text-lg animate-pulse delay-300">✨</div>
        <div className="absolute top-16 right-10 text-2xl animate-pulse delay-500">🌙</div>
      </div>

      {/* 标题区 */}
      <div className="pt-12 pb-6 text-center z-10">
        <h1 className="text-3xl font-bold tracking-wider text-indigo-200 mb-2 drop-shadow-md">
          晚安，宝 <span className="inline-block animate-bounce text-2xl">💤</span>
        </h1>
        <p className="text-indigo-300/70 text-sm">夜深了，来点助眠的小魔法吧</p>
      </div>

      {/* 导航栏 */}
      <div className="flex justify-center gap-2 px-4 mb-8 z-10">
        {[
          { id: 'breathe', icon: '💨', label: '深呼吸' },
          { id: 'sheep', icon: '🐑', label: '数绵羊' },
          { id: 'whispers', icon: '💌', label: '悄悄话' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 flex items-center gap-2
              ${activeTab === tab.id 
                ? 'bg-indigo-500/30 text-indigo-100 shadow-[0_0_15px_rgba(99,102,241,0.3)]' 
                : 'bg-white/5 text-indigo-300/50 hover:bg-white/10'}`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* 内容区 */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 pb-20 z-10">
        
        {/* 1. 呼吸模式 */}
        {activeTab === 'breathe' && (
          <div className="flex flex-col items-center">
            <div className="relative w-64 h-64 flex items-center justify-center mb-8">
              {/* 外圈光晕 */}
              <div 
                className={`absolute bg-indigo-500/20 rounded-full blur-xl transition-all duration-[4000ms] ease-in-out
                  ${isBreathingIn ? 'w-64 h-64 opacity-60' : 'w-32 h-32 opacity-20'}`}
              />
              {/* 内圈实体 */}
              <div 
                className={`absolute bg-gradient-to-tr from-indigo-400/40 to-purple-400/40 rounded-full backdrop-blur-sm border border-white/10 transition-all duration-[4000ms] ease-in-out flex items-center justify-center shadow-lg
                  ${isBreathingIn ? 'w-48 h-48' : 'w-24 h-24'}`}
              >
                <span className="text-indigo-100 text-lg font-medium tracking-widest drop-shadow-md transition-opacity duration-500">
                  {isBreathingIn ? '吸气...' : '呼气...'}
                </span>
              </div>
            </div>
            <p className="text-indigo-300/80 text-center text-sm leading-relaxed max-w-xs">
              跟着光晕的节奏，<br/>把一天的疲惫都轻轻吐出去...
            </p>
          </div>
        )}

        {/* 2. 数绵羊模式 */}
        {activeTab === 'sheep' && (
          <div className="flex flex-col items-center w-full relative">
            {/* 飘浮的绵羊动画 */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden h-64 -top-32">
              {floatingItems.map(item => (
                <div 
                  key={item.id}
                  className="absolute text-4xl animate-[floatUp_3s_ease-in-out_forwards] opacity-0"
                  style={{ left: `${item.left}%` }}
                >
                  {item.emoji}
                </div>
              ))}
            </div>

            <style>{`
              @keyframes floatUp {
                0% { transform: translateY(50px) scale(0.5); opacity: 0; }
                20% { opacity: 1; }
                80% { opacity: 0.8; }
                100% { transform: translateY(-150px) scale(1.2); opacity: 0; }
              }
            `}</style>

            <div className="text-6xl font-light text-indigo-200 mb-2 drop-shadow-[0_0_10px_rgba(199,210,254,0.5)]">
              {sheepCount}
            </div>
            <p className="text-indigo-400/60 text-sm mb-12">只软绵绵的小羊</p>

            <button 
              onClick={handleCountSheep}
              className="group relative px-8 py-4 bg-indigo-500/20 hover:bg-indigo-400/30 active:bg-indigo-600/40 border border-indigo-300/20 rounded-3xl transition-all duration-200 overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <span className="relative z-10 flex items-center gap-3 text-lg font-medium text-indigo-100">
                <span>跳过围栏</span>
                <span className="text-2xl group-active:translate-x-2 group-active:-translate-y-2 transition-transform">🐑</span>
              </span>
            </button>
          </div>
        )}

        {/* 3. 悄悄话模式 */}
        {activeTab === 'whispers' && (
          <div className="flex flex-col items-center w-full max-w-sm">
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 mb-8 shadow-2xl relative min-h-[160px] flex items-center justify-center">
              <div className="absolute -top-4 -left-4 text-4xl opacity-50">💌</div>
              <p className="text-lg text-indigo-100 leading-relaxed text-center font-medium">
                {WHISPERS[whisperIndex]}
              </p>
            </div>

            <button 
              onClick={handleNextWhisper}
              className="px-6 py-3 bg-white/10 hover:bg-white/15 rounded-full text-sm text-indigo-200 transition-colors flex items-center gap-2 border border-white/5"
            >
              <span>再听一句</span>
              <span className="animate-pulse">💖</span>
            </button>
          </div>
        )}

      </div>
    </div>
  );
}