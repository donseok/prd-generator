"use client";

import React from "react";

/* ─────────────────────────────────────────────
   HeroBackground
   히어로 섹션 위에 position:absolute 로 오버레이.
   인라인 SVG + keyframe CSS animation 사용.
   opacity 낮게 → 배경 장식 느낌.
───────────────────────────────────────────── */

const KEYFRAMES = `
@keyframes hb-float-a {
  0%,100% { transform: translateY(0px) rotate(0deg); }
  33%      { transform: translateY(-10px) rotate(4deg); }
  66%      { transform: translateY(5px) rotate(-3deg); }
}
@keyframes hb-float-b {
  0%,100% { transform: translateY(0px) rotate(0deg); }
  40%      { transform: translateY(8px) rotate(-5deg); }
  80%      { transform: translateY(-6px) rotate(3deg); }
}
@keyframes hb-float-c {
  0%,100% { transform: translateY(0px) scale(1); }
  50%      { transform: translateY(-14px) scale(1.06); }
}
@keyframes hb-pulse-ring {
  0%,100% { transform: scale(1); opacity:0.18; }
  50%      { transform: scale(1.12); opacity:0.06; }
}
@keyframes hb-drift {
  0%,100% { transform: translate(0,0) rotate(0deg); }
  25%      { transform: translate(6px,-8px) rotate(6deg); }
  75%      { transform: translate(-5px,6px) rotate(-4deg); }
}
@keyframes hb-spin-slow {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
`;

/* 각 장식 요소 데이터 */
interface ShapeItem {
  id: string;
  x: string;   // left %
  y: string;   // top %
  size: number;
  color: string;
  anim: string;
  delay: string;
  duration: string;
  opacity: number;
  shape: "doc" | "hex" | "circle-ring" | "diamond" | "triangle" | "grid" | "bracket" | "cross";
}

const SHAPES: ShapeItem[] = [
  // 왼쪽 상단
  { id:"s1", x:"5%",  y:"8%",  size:44, color:"#5de4c7", anim:"hb-float-a",    delay:"0s",    duration:"7s",  opacity:0.18, shape:"doc" },
  { id:"s2", x:"12%", y:"70%", size:32, color:"#f0b775", anim:"hb-float-b",    delay:"1.2s",  duration:"9s",  opacity:0.14, shape:"diamond" },
  { id:"s3", x:"2%",  y:"42%", size:56, color:"#5de4c7", anim:"hb-pulse-ring", delay:"0.4s",  duration:"6s",  opacity:0.12, shape:"circle-ring" },

  // 상단 중앙
  { id:"s4", x:"28%", y:"5%",  size:28, color:"#f0b775", anim:"hb-drift",      delay:"2s",    duration:"11s", opacity:0.13, shape:"hex" },
  { id:"s5", x:"36%", y:"82%", size:20, color:"#5de4c7", anim:"hb-float-a",    delay:"0.8s",  duration:"8s",  opacity:0.15, shape:"cross" },

  // 오른쪽 상단 (통계 카드 위)
  { id:"s6", x:"72%", y:"4%",  size:38, color:"#5de4c7", anim:"hb-float-c",    delay:"0s",    duration:"10s", opacity:0.14, shape:"doc" },
  { id:"s7", x:"82%", y:"14%", size:24, color:"#f0b775", anim:"hb-float-b",    delay:"1.6s",  duration:"7s",  opacity:0.16, shape:"triangle" },
  { id:"s8", x:"90%", y:"50%", size:48, color:"#5de4c7", anim:"hb-pulse-ring", delay:"2.2s",  duration:"8s",  opacity:0.10, shape:"circle-ring" },
  { id:"s9", x:"78%", y:"72%", size:30, color:"#f0b775", anim:"hb-drift",      delay:"0.6s",  duration:"12s", opacity:0.12, shape:"hex" },

  // 우하단
  { id:"s10",x:"94%", y:"80%", size:22, color:"#5de4c7", anim:"hb-float-a",   delay:"3s",    duration:"9s",  opacity:0.14, shape:"diamond" },

  // 그리드 도트 (배경 텍스처 느낌)
  { id:"s11",x:"55%", y:"15%", size:60, color:"#5de4c7", anim:"hb-float-b",   delay:"1s",    duration:"14s", opacity:0.07, shape:"grid" },
  { id:"s12",x:"18%", y:"28%", size:50, color:"#f0b775", anim:"hb-drift",     delay:"2.5s",  duration:"13s", opacity:0.07, shape:"grid" },

  // 브라켓 기호
  { id:"s13",x:"48%", y:"60%", size:36, color:"#f0b775", anim:"hb-float-c",   delay:"0.3s",  duration:"10s", opacity:0.13, shape:"bracket" },
  { id:"s14",x:"62%", y:"88%", size:28, color:"#5de4c7", anim:"hb-float-a",   delay:"1.8s",  duration:"8s",  opacity:0.12, shape:"doc" },
];

/* ── 개별 SVG 모양 렌더러 ── */
function ShapeSVG({ shape, size, color }: { shape: ShapeItem["shape"]; size: number; color: string }) {
  const s = size;
  switch (shape) {
    /* 문서 아이콘 */
    case "doc":
      return (
        <svg width={s} height={s * 1.25} viewBox="0 0 40 50" fill="none">
          <rect x="2" y="2" width="36" height="46" rx="4" stroke={color} strokeWidth="2" fill="none"/>
          <path d="M24 2v12h14" stroke={color} strokeWidth="2"/>
          <line x1="8" y1="22" x2="32" y2="22" stroke={color} strokeWidth="2" strokeLinecap="round"/>
          <line x1="8" y1="30" x2="32" y2="30" stroke={color} strokeWidth="2" strokeLinecap="round"/>
          <line x1="8" y1="38" x2="22" y2="38" stroke={color} strokeWidth="2" strokeLinecap="round"/>
        </svg>
      );

    /* 육각형 */
    case "hex":
      return (
        <svg width={s} height={s} viewBox="0 0 40 40" fill="none">
          <polygon
            points="20,2 36,11 36,29 20,38 4,29 4,11"
            stroke={color} strokeWidth="2" fill="none"
          />
          <polygon
            points="20,10 30,15.5 30,26.5 20,32 10,26.5 10,15.5"
            stroke={color} strokeWidth="1.2" fill="none" opacity="0.5"
          />
        </svg>
      );

    /* 링 */
    case "circle-ring":
      return (
        <svg width={s} height={s} viewBox="0 0 60 60" fill="none">
          <circle cx="30" cy="30" r="26" stroke={color} strokeWidth="1.5" fill="none" strokeDasharray="6 4"/>
          <circle cx="30" cy="30" r="16" stroke={color} strokeWidth="1" fill="none" opacity="0.5"/>
          <circle cx="30" cy="30" r="4" fill={color} opacity="0.4"/>
        </svg>
      );

    /* 다이아몬드 */
    case "diamond":
      return (
        <svg width={s} height={s} viewBox="0 0 40 40" fill="none">
          <rect x="6" y="6" width="28" height="28" rx="2" stroke={color} strokeWidth="2" fill="none"
            transform="rotate(45 20 20)"/>
        </svg>
      );

    /* 삼각형 */
    case "triangle":
      return (
        <svg width={s} height={s} viewBox="0 0 40 40" fill="none">
          <polygon points="20,4 36,34 4,34" stroke={color} strokeWidth="2" fill="none"/>
          <polygon points="20,12 30,30 10,30" stroke={color} strokeWidth="1" fill="none" opacity="0.45"/>
        </svg>
      );

    /* 3×3 도트 그리드 */
    case "grid": {
      const gap = s / 4;
      const r = s / 16;
      const dots: React.ReactNode[] = [];
      for (let row = 0; row < 3; row++) {
        for (let col = 0; col < 3; col++) {
          dots.push(
            <circle key={`${row}-${col}`}
              cx={gap + col * gap} cy={gap + row * gap} r={r}
              fill={color}
            />
          );
        }
      }
      return <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} fill="none">{dots}</svg>;
    }

    /* 코드 브라켓 { } */
    case "bracket":
      return (
        <svg width={s} height={s * 1.1} viewBox="0 0 44 48" fill="none">
          <path d="M14 4 C8 4 6 8 6 12 L6 20 C6 24 2 24 2 24 C2 24 6 24 6 28 L6 36 C6 40 8 44 14 44"
            stroke={color} strokeWidth="2.2" strokeLinecap="round" fill="none"/>
          <path d="M30 4 C36 4 38 8 38 12 L38 20 C38 24 42 24 42 24 C42 24 38 24 38 28 L38 36 C38 40 36 44 30 44"
            stroke={color} strokeWidth="2.2" strokeLinecap="round" fill="none"/>
          <circle cx="22" cy="24" r="2" fill={color} opacity="0.5"/>
        </svg>
      );

    /* 십자/플러스 */
    case "cross":
      return (
        <svg width={s} height={s} viewBox="0 0 40 40" fill="none">
          <line x1="20" y1="4"  x2="20" y2="36" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
          <line x1="4"  y1="20" x2="36" y2="20" stroke={color} strokeWidth="2.5" strokeLinecap="round"/>
          <line x1="20" y1="4"  x2="20" y2="36" stroke={color} strokeWidth="1"   strokeLinecap="round"
            transform="rotate(45 20 20)" opacity="0.4"/>
          <line x1="4"  y1="20" x2="36" y2="20" stroke={color} strokeWidth="1"   strokeLinecap="round"
            transform="rotate(45 20 20)" opacity="0.4"/>
        </svg>
      );

    default:
      return null;
  }
}

/* ── 메인 컴포넌트 ── */
export function HeroBackground() {
  return (
    <>
      {/* keyframe 주입 */}
      <style dangerouslySetInnerHTML={{ __html: KEYFRAMES }} />

      {/* 오버레이 컨테이너 */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          overflow: "hidden",
          zIndex: 0,
        }}
      >
        {SHAPES.map((item) => (
          <div
            key={item.id}
            style={{
              position: "absolute",
              left: item.x,
              top: item.y,
              opacity: item.opacity,
              animation: `${item.anim} ${item.duration} ease-in-out ${item.delay} infinite`,
              willChange: "transform",
            }}
          >
            <ShapeSVG shape={item.shape} size={item.size} color={item.color} />
          </div>
        ))}

        {/* 미세 그라데이션 글로우 – mint 좌하단 */}
        <div
          style={{
            position: "absolute",
            bottom: "-20%",
            left: "0%",
            width: "40%",
            height: "80%",
            background: "radial-gradient(ellipse at center, rgba(93,228,199,0.07) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />

        {/* 미세 그라데이션 글로우 – warm 우상단 */}
        <div
          style={{
            position: "absolute",
            top: "-20%",
            right: "0%",
            width: "40%",
            height: "80%",
            background: "radial-gradient(ellipse at center, rgba(240,183,117,0.06) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />
      </div>
    </>
  );
}
