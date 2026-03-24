"use client";

/**
 * HeroOrbs — 히어로 섹션 배경 장식 컴포넌트
 *
 * 글래스모피즘/블러 기반 추상 빛 orb.
 * position: absolute, pointer-events: none — 순수 장식용.
 * 부모 히어로 섹션에 position: relative + overflow: hidden 필요.
 */
export function HeroOrbs() {
  return (
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
      {/* ── 스타일 정의 ── */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes orb-breathe {
          0%, 100% { transform: scale(1) translate(0, 0); opacity: 0.55; }
          33%       { transform: scale(1.12) translate(6px, -8px); opacity: 0.72; }
          66%       { transform: scale(0.94) translate(-4px, 6px); opacity: 0.48; }
        }
        @keyframes orb-drift {
          0%, 100% { transform: scale(1) translate(0, 0) rotate(0deg); opacity: 0.4; }
          40%       { transform: scale(1.08) translate(-10px, 8px) rotate(8deg); opacity: 0.6; }
          80%       { transform: scale(0.96) translate(8px, -5px) rotate(-4deg); opacity: 0.35; }
        }
        @keyframes orb-pulse {
          0%, 100% { transform: scale(1); opacity: 0.28; }
          50%       { transform: scale(1.18); opacity: 0.48; }
        }
        @keyframes streak-fade {
          0%, 100% { opacity: 0; transform: translateY(0) rotate(-28deg) scaleX(1); }
          20%       { opacity: 0.18; }
          50%       { opacity: 0.32; transform: translateY(-10px) rotate(-28deg) scaleX(1.06); }
          80%       { opacity: 0.14; }
        }
        @keyframes streak-fade-2 {
          0%, 100% { opacity: 0; transform: translateY(0) rotate(-18deg) scaleX(1); }
          25%       { opacity: 0.22; }
          55%       { opacity: 0.28; transform: translateY(-8px) rotate(-18deg) scaleX(1.04); }
          85%       { opacity: 0.1; }
        }
        @keyframes particle-float {
          0%, 100% { transform: translateY(0) translateX(0) scale(1); opacity: 0; }
          15%       { opacity: 0.7; }
          50%       { transform: translateY(-22px) translateX(6px) scale(1.2); opacity: 0.5; }
          85%       { opacity: 0.2; }
        }
        @keyframes particle-float-2 {
          0%, 100% { transform: translateY(0) translateX(0) scale(0.8); opacity: 0; }
          20%       { opacity: 0.6; }
          55%       { transform: translateY(-18px) translateX(-8px) scale(1.1); opacity: 0.4; }
          90%       { opacity: 0.1; }
        }
        @keyframes ring-expand {
          0%   { transform: scale(0.85); opacity: 0.22; }
          50%  { transform: scale(1.05); opacity: 0.12; }
          100% { transform: scale(0.85); opacity: 0.22; }
        }
      ` }} />

      {/* ── Orb 1: 민트 대형 — 오른쪽 상단 ── */}
      <div
        style={{
          position: "absolute",
          top: "-80px",
          right: "-60px",
          width: "420px",
          height: "420px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle at 40% 40%, rgba(93,228,199,0.38) 0%, rgba(93,228,199,0.14) 50%, transparent 72%)",
          filter: "blur(52px)",
          animation: "orb-breathe 9s ease-in-out infinite",
        }}
      />

      {/* ── Orb 2: 웜 오렌지 중형 — 오른쪽 중앙 ── */}
      <div
        style={{
          position: "absolute",
          top: "30px",
          right: "80px",
          width: "280px",
          height: "280px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle at 55% 45%, rgba(240,183,117,0.32) 0%, rgba(240,183,117,0.10) 55%, transparent 75%)",
          filter: "blur(40px)",
          animation: "orb-drift 12s ease-in-out infinite",
          animationDelay: "-3.5s",
        }}
      />

      {/* ── Orb 3: 민트 소형 코어 글로우 — 오른쪽 상단 내측 ── */}
      <div
        style={{
          position: "absolute",
          top: "20px",
          right: "60px",
          width: "140px",
          height: "140px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(93,228,199,0.55) 0%, rgba(93,228,199,0.22) 45%, transparent 70%)",
          filter: "blur(18px)",
          animation: "orb-pulse 6s ease-in-out infinite",
          animationDelay: "-1.2s",
        }}
      />

      {/* ── Orb 4: 딥 블루 보조 — 오른쪽 하단 ── */}
      <div
        style={{
          position: "absolute",
          bottom: "-30px",
          right: "20px",
          width: "240px",
          height: "240px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle at 50% 50%, rgba(121,174,218,0.22) 0%, rgba(121,174,218,0.07) 55%, transparent 75%)",
          filter: "blur(44px)",
          animation: "orb-breathe 14s ease-in-out infinite",
          animationDelay: "-6s",
        }}
      />

      {/* ── 빛줄기 1: 민트 사선 ── */}
      <div
        style={{
          position: "absolute",
          top: "-20px",
          right: "100px",
          width: "3px",
          height: "260px",
          background:
            "linear-gradient(to bottom, transparent 0%, rgba(93,228,199,0.55) 35%, rgba(93,228,199,0.70) 60%, transparent 100%)",
          borderRadius: "2px",
          filter: "blur(2.5px)",
          animation: "streak-fade 7s ease-in-out infinite",
          animationDelay: "-1s",
        }}
      />

      {/* ── 빛줄기 2: 웜 사선 ── */}
      <div
        style={{
          position: "absolute",
          top: "10px",
          right: "180px",
          width: "2px",
          height: "180px",
          background:
            "linear-gradient(to bottom, transparent 0%, rgba(240,183,117,0.45) 30%, rgba(240,183,117,0.60) 65%, transparent 100%)",
          borderRadius: "2px",
          filter: "blur(2px)",
          animation: "streak-fade-2 9s ease-in-out infinite",
          animationDelay: "-4s",
        }}
      />

      {/* ── 빛줄기 3: 가는 민트 ── */}
      <div
        style={{
          position: "absolute",
          top: "40px",
          right: "240px",
          width: "1.5px",
          height: "120px",
          background:
            "linear-gradient(to bottom, transparent 0%, rgba(93,228,199,0.35) 40%, rgba(93,228,199,0.50) 70%, transparent 100%)",
          borderRadius: "2px",
          filter: "blur(1.5px)",
          animation: "streak-fade 11s ease-in-out infinite",
          animationDelay: "-7s",
        }}
      />

      {/* ── 파티클 1 ── */}
      <div
        style={{
          position: "absolute",
          top: "90px",
          right: "130px",
          width: "5px",
          height: "5px",
          borderRadius: "50%",
          background: "rgba(93,228,199,0.9)",
          boxShadow: "0 0 8px 3px rgba(93,228,199,0.45)",
          animation: "particle-float 5.5s ease-in-out infinite",
        }}
      />

      {/* ── 파티클 2 ── */}
      <div
        style={{
          position: "absolute",
          top: "55px",
          right: "210px",
          width: "4px",
          height: "4px",
          borderRadius: "50%",
          background: "rgba(240,183,117,0.85)",
          boxShadow: "0 0 6px 2px rgba(240,183,117,0.40)",
          animation: "particle-float-2 7s ease-in-out infinite",
          animationDelay: "-2s",
        }}
      />

      {/* ── 파티클 3 ── */}
      <div
        style={{
          position: "absolute",
          top: "120px",
          right: "300px",
          width: "3px",
          height: "3px",
          borderRadius: "50%",
          background: "rgba(93,228,199,0.7)",
          boxShadow: "0 0 5px 2px rgba(93,228,199,0.35)",
          animation: "particle-float 8s ease-in-out infinite",
          animationDelay: "-5s",
        }}
      />

      {/* ── 파티클 4 ── */}
      <div
        style={{
          position: "absolute",
          top: "70px",
          right: "165px",
          width: "3.5px",
          height: "3.5px",
          borderRadius: "50%",
          background: "rgba(121,174,218,0.75)",
          boxShadow: "0 0 6px 2px rgba(121,174,218,0.35)",
          animation: "particle-float-2 6.5s ease-in-out infinite",
          animationDelay: "-3s",
        }}
      />

      {/* ── 링 글로우 (투명 테두리 원) ── */}
      <div
        style={{
          position: "absolute",
          top: "-40px",
          right: "-40px",
          width: "340px",
          height: "340px",
          borderRadius: "50%",
          border: "1.5px solid rgba(93,228,199,0.20)",
          background: "transparent",
          animation: "ring-expand 10s ease-in-out infinite",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "-10px",
          right: "-10px",
          width: "240px",
          height: "240px",
          borderRadius: "50%",
          border: "1px solid rgba(240,183,117,0.15)",
          background: "transparent",
          animation: "ring-expand 13s ease-in-out infinite",
          animationDelay: "-4s",
        }}
      />
    </div>
  );
}
