import React, { useState, useEffect, useRef } from "react";

const N = { X: { x: 150, y: 50 }, Y: { x: 58, y: 188 }, Z: { x: 242, y: 188 } };
const CYCLE = [["X", "Y", 1], ["Y", "Z", -3], ["Z", "X", 1]]; // 一圈 = -1
const START = 3;

function shorten(a, b, pad) {
  const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy);
  return {
    x1: a.x + (dx / len) * pad, y1: a.y + (dy / len) * pad,
    x2: b.x - (dx / len) * pad, y2: b.y - (dy / len) * pad,
    mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2,
  };
}

export default function NegCycle() {
  const [n, setN] = useState(0);
  const [spin, setSpin] = useState(false);
  const [auto, setAuto] = useState(false);
  const timer = useRef(null);
  const dist = START - n;

  const round = () => { setN((v) => v + 1); setSpin(true); setTimeout(() => setSpin(false), 420); };
  useEffect(() => {
    if (!auto) return;
    timer.current = setInterval(round, 520);
    return () => clearInterval(timer.current);
  }, [auto]);

  const distColor = dist > 0 ? "#4ade80" : dist === 0 ? "#fbbf24" : "#ff7849";
  let line;
  if (n === 0) line = "假设你刚走到 X，到这儿花了 3 块成本。现在……敢绕一圈吗？";
  else if (dist > 0) line = `绕了 ${n} 圈，成本降到 ${dist}。继续薅 👇`;
  else if (dist === 0) line = "归零！再绕下去，就开始倒贴钱给你了——";
  else line = `已经凭空薅了 ${-dist} 块 😈 而且还能继续，永远停不下来。这就是「负无穷」长的样子。`;

  const C = { bg: "#0a0e1a", panel: "#121a30", border: "#222d4d", text: "#e8edf7", dim: "#7e89a8", gold: "#fbbf24" };

  return (
    <div style={{ background: C.bg, minHeight: "100%", padding: 16, fontFamily: "'JetBrains Mono', ui-monospace, monospace", color: C.text }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        @keyframes flow { to { stroke-dashoffset: -24 } }
      `}</style>
      <div style={{ maxWidth: 380, margin: "0 auto" }}>
        <div style={{ fontSize: 11, letterSpacing: 1.5, color: C.dim }}>NEGATIVE CYCLE</div>
        <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 10 }}>负权回路 = 无限刷钱 🪙</div>

        <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 12, padding: 8, marginBottom: 12 }}>
          <svg viewBox="0 0 300 240" style={{ width: "100%", display: "block" }}>
            <defs>
              <marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
                <path d="M0,0 L9,4.5 L0,9 z" fill={spin ? C.gold : "#7a6326"} />
              </marker>
              <filter id="g" x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur stdDeviation="3" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
            </defs>
            {CYCLE.map(([a, b, w], k) => {
              const s = shorten(N[a], N[b], 24);
              return (
                <line key={k} x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2}
                  stroke={spin ? C.gold : "#3f4060"} strokeWidth={spin ? 3.5 : 2}
                  markerEnd="url(#arrow)" strokeDasharray={spin ? "7 5" : "0"}
                  style={spin ? { animation: "flow .7s linear infinite" } : undefined}
                  filter={spin ? "url(#g)" : undefined} />
              );
            })}
            {CYCLE.map(([a, b, w], k) => {
              const s = shorten(N[a], N[b], 24);
              const off = a === "Y" ? -16 : 16;
              return (
                <g key={"w" + k}>
                  <circle cx={s.mx + (a === "X" ? 14 : a === "Y" ? 0 : -14)} cy={s.my + (a === "Y" ? 16 : -4)} r={12} fill={C.bg} stroke="#3f4060" />
                  <text x={s.mx + (a === "X" ? 14 : a === "Y" ? 0 : -14)} y={s.my + (a === "Y" ? 20 : 0)} textAnchor="middle" fontSize={12} fontWeight={700} fill={w < 0 ? "#ff7849" : "#9aa6c8"}>{w > 0 ? "+" + w : w}</text>
                </g>
              );
            })}
            <text x={150} y={138} textAnchor="middle" fontSize={11} fill={C.dim}>一圈 =</text>
            <text x={150} y={156} textAnchor="middle" fontSize={13} fontWeight={700} fill="#ff7849">+1 −3 +1 = −1</text>
            {Object.entries(N).map(([id, p]) => (
              <g key={id}>
                <circle cx={p.x} cy={p.y} r={22} fill="#1a2238" stroke={C.gold} strokeWidth={2} filter={spin ? "url(#g)" : undefined} />
                <text x={p.x} y={p.y + 6} textAnchor="middle" fontSize={17} fontWeight={700} fill={C.text}>{id}</text>
              </g>
            ))}
          </svg>
        </div>

        {/* 计数器 */}
        <div style={{ background: "#0f1626", border: `1px solid ${C.border}`, borderRadius: 12, padding: "14px 12px", textAlign: "center", marginBottom: 10 }}>
          <div style={{ fontSize: 11, color: C.dim }}>到 X 的累计成本 / 距离</div>
          <div style={{ fontSize: 44, fontWeight: 700, color: distColor, lineHeight: 1.15, transition: "color .2s" }}>{dist}</div>
          <div style={{ fontSize: 11, color: C.dim }}>已绕 {n} 圈{dist < 0 ? " · ↓ 还能更低，没有底" : ""}</div>
        </div>

        <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 12px", fontSize: 13, lineHeight: 1.5, minHeight: 44, marginBottom: 12 }}>{line}</div>

        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={round} style={{ flex: 1, padding: "11px 6px", borderRadius: 10, fontSize: 13, fontWeight: 700, border: `1px solid ${C.gold}`, background: "#2a2110", color: C.gold, cursor: "pointer", fontFamily: "inherit" }}>🔁 再绕一圈</button>
          <button onClick={() => setAuto((a) => !a)} style={{ flex: 1, padding: "11px 6px", borderRadius: 10, fontSize: 13, fontWeight: 600, border: `1px solid ${C.border}`, background: auto ? "#2a2110" : "#172138", color: auto ? C.gold : C.text, cursor: "pointer", fontFamily: "inherit" }}>{auto ? "⏸ 停下" : "▶ 自动狂绕"}</button>
        </div>
        <button onClick={() => { setAuto(false); setN(0); }} style={{ width: "100%", marginTop: 8, padding: 8, borderRadius: 9, fontSize: 12, color: C.dim, background: "transparent", border: `1px solid ${C.border}`, cursor: "pointer", fontFamily: "inherit" }}>重置</button>
      </div>
    </div>
  );
}
