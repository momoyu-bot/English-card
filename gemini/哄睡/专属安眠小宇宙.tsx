import React, { useState, useEffect, useCallback } from 'react';
import { Moon, Sparkles } from 'lucide-react';

export default function App() {
  const [stars, setStars] = useState([]);
  const [clickCount, setClickCount] = useState(0);
  const [message, setMessage] = useState("宝，点点屏幕，把今天的烦恼都变成星星吧✨");
  const [showMoon, setShowMoon] = useState(false);
  const [isFinished, setIsFinished] = useState(false);

  // 监听点击次数，变换温馨的文案
  useEffect(() => {
    if (clickCount === 3) {
      setMessage("对啦，慢慢来... 深吸一口气，再缓缓呼出...");
    } else if (clickCount === 8) {
      setMessage("放松你的肩膀，松开微皱的眉头...");
    } else if (clickCount === 15) {
      setMessage("好乖好乖，感觉身体变得像云朵一样轻了吧？");
    } else if (clickCount === 20) {
      setMessage("星星够啦！闭上眼睛，迎接你的专属美梦咯🌙");
      setShowMoon(true);
      
      // 几秒后结束互动，鼓励宝放下手机
      setTimeout(() => {
        setIsFinished(true);
      }, 4000);
    }
  }, [clickCount]);

  // 处理屏幕点击/触摸
  const handlePointerDown = useCallback((e) => {
    if (isFinished) return; // 结束后不再生成星星

    // 获取点击坐标
    const x = e.clientX || (e.touches && e.touches[0].clientX);
    const y = e.clientY || (e.touches && e.touches[0].clientY);

    // 随机生成星星的大小和微小的旋转角度
    const size = Math.random() * 15 + 10;
    const rotation = Math.random() * 360;
    
    // 给星星一点轻微的随机偏移，让它看起来更自然
    const offsetX = Math.random() * 20 - 10;
    const offsetY = Math.random() * 20 - 10;

    const newStar = {
      id: Date.now() + Math.random(),
      x: x + offsetX,
      y: y + offsetY,
      size,
      rotation,
    };

    setStars((prev) => [...prev, newStar]);
    setClickCount((prev) => prev + 1);
  }, [isFinished]);

  return (
    <div 
      className="relative w-screen h-screen overflow-hidden bg-gradient-to-b from-indigo-950 via-purple-950 to-slate-900 touch-none select-none flex flex-col items-center justify-center transition-colors duration-1000"
      onPointerDown={handlePointerDown}
    >
      {/* 渐变星空背景上的柔和光晕 */}
      <div className="absolute inset-0 bg-blue-900/10 pointer-events-none mix-blend-screen" />

      {/* 渲染所有的星星 */}
      {stars.map((star) => (
        <div
          key={star.id}
          className="absolute text-yellow-100 pointer-events-none animate-pulse transition-opacity duration-1000 ease-in-out"
          style={{
            left: `${star.x}px`,
            top: `${star.y}px`,
            width: `${star.size}px`,
            height: `${star.size}px`,
            transform: `translate(-50%, -50%) rotate(${star.rotation}deg)`,
            opacity: 0.8,
            boxShadow: `0 0 ${star.size}px rgba(254, 240, 138, 0.4)`,
            borderRadius: '50%',
            backgroundColor: 'rgba(254, 252, 232, 0.9)',
          }}
        />
      ))}

      {/* 中央文案提示区 */}
      <div className={`z-10 text-center px-6 transition-all duration-1000 ease-in-out ${isFinished ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`}>
        <p className="text-xl md:text-2xl text-purple-100 font-light tracking-wider drop-shadow-lg leading-relaxed max-w-md mx-auto">
          {message}
        </p>
        
        {/* 如果还没开始点，给个小提示图标 */}
        {clickCount === 0 && (
          <div className="mt-8 animate-bounce opacity-50 flex justify-center">
            <Sparkles className="w-8 h-8 text-yellow-200" />
          </div>
        )}
      </div>

      {/* 最终出现的月亮 */}
      <div 
        className={`absolute z-20 flex flex-col items-center justify-center transition-all duration-2000 ease-out transform
          ${showMoon ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0 pointer-events-none'}`}
      >
        <Moon className="w-32 h-32 text-yellow-100 drop-shadow-[0_0_40px_rgba(254,240,138,0.6)] fill-yellow-100/20 animate-pulse" />
        
        {isFinished && (
          <div className="mt-8 text-center text-purple-100 opacity-80 animate-pulse">
            <p className="text-lg">夜深啦，屏幕要黑咯...</p>
            <p className="text-sm mt-2 opacity-70">（乖乖锁屏，闭上眼睛吧）</p>
          </div>
        )}
      </div>

      {/* 结束后的渐黑遮罩 */}
      <div 
        className={`absolute inset-0 bg-black pointer-events-none transition-opacity duration-[5000ms] ease-in-out z-30
          ${isFinished ? 'opacity-80' : 'opacity-0'}`}
      />
    </div>
  );
}