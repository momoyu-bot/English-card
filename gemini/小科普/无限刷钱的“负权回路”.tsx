import React, { useState, useEffect, useRef } from 'react';
import { Home, Store, Film, Sparkles, AlertTriangle, RefreshCw, HandCoins, Info } from 'lucide-react';

const NODES = {
  home: { id: 'home', label: '家 (起点)', x: 150, y: 50, icon: Home },
  shop: { id: 'shop', label: '商场', x: 60, y: 160, icon: Store },
  cinema: { id: 'cinema', label: '电影院', x: 240, y: 160, icon: Film },
  park: { id: 'park', label: '游乐园 (终点)', x: 150, y: 270, icon: Sparkles }
};

const EDGES = [
  { from: 'home', to: 'shop', cost: -5, desc: '路费 -5', path: 'M 140 65 L 70 145', labelPos: {x: 85, y: 95}, color: 'text-gray-500' },
  { from: 'home', to: 'cinema', cost: -10, desc: '路费 -10', path: 'M 160 65 L 230 145', labelPos: {x: 215, y: 95}, color: 'text-gray-500' },
  
  // 这两条是负权回路的核心（正数代表赚钱/反向充电）
  { from: 'shop', to: 'cinema', cost: 15, desc: '赚 15!', path: 'M 75 155 Q 150 110 225 155', labelPos: {x: 150, y: 120}, color: 'text-green-500', isGlitch: true },
  { from: 'cinema', to: 'shop', cost: 10, desc: '赚 10!', path: 'M 225 165 Q 150 210 75 165', labelPos: {x: 150, y: 200}, color: 'text-green-500', isGlitch: true },
  
  { from: 'shop', to: 'park', cost: -20, desc: '路费 -20', path: 'M 70 175 L 140 255', labelPos: {x: 85, y: 230}, color: 'text-gray-500' },
  { from: 'cinema', to: 'park', cost: -20, desc: '路费 -20', path: 'M 230 175 L 160 255', labelPos: {x: 215, y: 230}, color: 'text-gray-500' },
];

export default function App() {
  const [current, setCurrent] = useState('home');
  const [coins, setCoins] = useState(50);
  const [history, setHistory] = useState(['home']);
  const [glitchCount, setGlitchCount] = useState(0);
  const [floatingText, setFloatingText] = useState(null);

  const endRef = useRef(null);

  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [history]);

  const handleTravel = (edge) => {
    setCoins(prev => prev + edge.cost);
    setCurrent(edge.to);
    setHistory(prev => [...prev, edge.to]);
    
    // 显示浮动文字动画
    setFloatingText({ cost: edge.cost, id: Date.now() });
    setTimeout(() => setFloatingText(null), 1000);

    // 记录卡bug次数
    if (edge.isGlitch) {
      setGlitchCount(prev => prev + 1);
    }
  };

  const resetGame = () => {
    setCurrent('home');
    setCoins(50);
    setHistory(['home']);
    setGlitchCount(0);
    setFloatingText(null);
  };

  // 找当前节点可以去的下一站
  const availableEdges = EDGES.filter(e => e.from === current);

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans text-slate-800 flex flex-col items-center">
      
      {/* 标题栏 */}
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6 text-center">
        <h1 className="text-2xl font-bold text-indigo-600 mb-2 flex items-center justify-center gap-2">
          <RefreshCw className="w-6 h-6" />
          宝的“无限刷钱”模拟器
        </h1>
        <p className="text-slate-500 text-sm">
          你的初始资金是 <strong className="text-yellow-600">50 金币</strong>。
          试试看能不能利用地图里的“特殊路段”，带着几百金币到达游乐园？
        </p>
      </div>

      {/* 核心游戏区 */}
      <div className="w-full max-w-lg bg-white rounded-3xl shadow-lg border border-slate-100 overflow-hidden relative">
        
        {/* 状态栏 */}
        <div className="bg-indigo-50 p-4 flex justify-between items-center border-b border-indigo-100">
          <div className="flex items-center gap-2">
            <div className="bg-yellow-400 text-yellow-900 p-2 rounded-xl">
              <HandCoins className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-indigo-400 font-bold uppercase tracking-wider">小金库</div>
              <div className="text-2xl font-black text-indigo-900 transition-all duration-300">
                {coins} <span className="text-sm font-medium text-indigo-400">币</span>
              </div>
            </div>
          </div>
          <button 
            onClick={resetGame}
            className="text-xs bg-white text-slate-500 hover:text-indigo-600 px-3 py-1.5 rounded-full shadow-sm font-medium transition-colors"
          >
            重新开始
          </button>
        </div>

        {/* 浮动加减钱动画 */}
        {floatingText && (
          <div 
            key={floatingText.id}
            className={`absolute top-20 left-1/2 -translate-x-1/2 text-2xl font-black z-50 animate-bounce ${
              floatingText.cost > 0 ? 'text-green-500' : 'text-red-500'
            }`}
            style={{ animation: 'bounceUp 1s ease-out forwards' }}
          >
            {floatingText.cost > 0 ? '+' : ''}{floatingText.cost}
          </div>
        )}

        {/* 地图区 */}
        <div className="relative w-full h-[340px] bg-slate-50">
          <svg className="w-full h-full" viewBox="0 0 300 320">
            <defs>
              <marker id="arrow-gray" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
              </marker>
              <marker id="arrow-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#22c55e" />
              </marker>
              
              {/* 光晕滤镜 */}
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* 画线 */}
            {EDGES.map((edge, idx) => (
              <g key={idx}>
                <path
                  d={edge.path}
                  fill="none"
                  stroke={edge.isGlitch ? "#22c55e" : "#94a3b8"}
                  strokeWidth="2"
                  strokeDasharray={edge.isGlitch ? "4 2" : ""}
                  markerEnd={`url(#arrow-${edge.isGlitch ? 'green' : 'gray'})`}
                  className={edge.isGlitch ? "animate-pulse" : ""}
                />
                <rect 
                  x={edge.labelPos.x - 22} 
                  y={edge.labelPos.y - 10} 
                  width="44" 
                  height="20" 
                  rx="4" 
                  fill="white" 
                  stroke={edge.isGlitch ? "#bbf7d0" : "#f1f5f9"}
                />
                <text 
                  x={edge.labelPos.x} 
                  y={edge.labelPos.y + 4} 
                  fontSize="8" 
                  fontWeight="bold"
                  textAnchor="middle" 
                  fill={edge.isGlitch ? "#16a34a" : "#64748b"}
                >
                  {edge.desc}
                </text>
              </g>
            ))}

            {/* 画节点 */}
            {Object.values(NODES).map(node => {
              const isCurrent = current === node.id;
              const isVisited = history.includes(node.id);
              
              return (
                <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
                  {isCurrent && (
                    <circle r="22" fill="none" stroke="#6366f1" strokeWidth="3" filter="url(#glow)" className="animate-ping" opacity="0.3" />
                  )}
                  <circle 
                    r="16" 
                    fill={isCurrent ? "#4f46e5" : (isVisited ? "#a5b4fc" : "#cbd5e1")} 
                    stroke={isCurrent ? "#312e81" : "white"}
                    strokeWidth="2"
                  />
                  <text 
                    y="28" 
                    fontSize="10" 
                    fontWeight="bold" 
                    textAnchor="middle" 
                    fill={isCurrent ? "#4f46e5" : "#475569"}
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* 控制面板区 */}
        <div className="bg-white p-5 border-t border-slate-100 min-h-[140px]">
          {current === 'park' ? (
            <div className="text-center animate-fade-in">
              <div className="inline-block p-3 bg-green-100 text-green-600 rounded-full mb-3">
                <Sparkles className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-slate-800">抵达游乐园！</h3>
              <p className="text-slate-600 mt-2">
                你最终带着 <strong className="text-indigo-600 text-lg">{coins}</strong> 金币到达了终点！
              </p>
              {glitchCount > 2 && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl flex gap-3 text-left">
                  <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0" />
                  <div className="text-sm text-red-800">
                    <strong>系统崩溃警告！</strong><br/>
                    Dijkstra 算法查监控发现你在商场和电影院之间来回跑了 {glitchCount} 次，薅了系统的羊毛！它的 CPU 已经烧了！🤯
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div>
              <div className="text-sm font-bold text-slate-400 mb-3 uppercase tracking-wider flex items-center gap-1">
                你在哪儿？ <span className="text-indigo-600">{NODES[current].label}</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {availableEdges.map((edge, idx) => {
                  const targetNode = NODES[edge.to];
                  const Icon = targetNode.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleTravel(edge)}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border-2 transition-all active:scale-95 ${
                        edge.isGlitch 
                          ? 'border-green-200 bg-green-50 hover:bg-green-100 text-green-700' 
                          : 'border-slate-100 bg-white hover:bg-slate-50 text-slate-700 hover:border-indigo-200 hover:text-indigo-600 shadow-sm'
                      }`}
                    >
                      <Icon className="w-6 h-6 mb-1 opacity-80" />
                      <span className="font-bold text-sm">去{targetNode.label}</span>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full mt-1 ${
                        edge.cost > 0 ? 'bg-green-200 text-green-800' : 'bg-slate-200 text-slate-600'
                      }`}>
                        {edge.cost > 0 ? '+' : ''}{edge.cost} 金币
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 讲解框 */}
      <div className="w-full max-w-lg mt-6 bg-blue-50/80 rounded-2xl p-4 border border-blue-100 flex gap-3 shadow-sm text-sm text-blue-900 leading-relaxed">
        <Info className="w-6 h-6 text-blue-500 flex-shrink-0" />
        <div>
          <strong>宝，这就是“负权回路”！</strong>
          <br/>
          只要商场去电影院赚 15，电影院回商场赚 10（虽然要扣别的费，但只要绕一圈总数是正的），你就可以无限走下去。
          对于 Dijkstra 这种死板的算法来说，它一旦觉得“到商场最少花 5 块，我已经知道了”，它就绝对想不到回头再去薅羊毛。于是它的世界观就崩塌啦！
        </div>
      </div>

      {/* CSS 动画注入 */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes bounceUp {
          0% { transform: translate(-50%, 0) scale(0.5); opacity: 0; }
          20% { transform: translate(-50%, -20px) scale(1.2); opacity: 1; }
          80% { transform: translate(-50%, -40px) scale(1); opacity: 1; }
          100% { transform: translate(-50%, -50px) scale(0.8); opacity: 0; }
        }
        .animate-fade-in {
          animation: fadeIn 0.5s ease-out forwards;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}} />
    </div>
  );
}