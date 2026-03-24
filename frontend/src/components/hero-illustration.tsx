"use client";

/**
 * HeroIllustration
 *
 * AI 문서 자동화 컨셉 SVG 일러스트.
 * - 문서 파싱 → AI 처리 → 산출물 변환 흐름을 시각화
 * - CSS keyframe 애니메이션 인라인 포함 (외부 파일 없음)
 * - prefers-reduced-motion 준수
 * - 다크/라이트 모드 공통 대응 (CSS 변수 기반)
 */
const HI_STYLES = `
        @media (prefers-reduced-motion: no-preference) {
          .hi-float {
            animation: hi-float 6s ease-in-out infinite;
          }
          .hi-float-slow {
            animation: hi-float 9s ease-in-out infinite reverse;
          }
          .hi-pulse-dot {
            animation: hi-pulse-dot 2.4s ease-in-out infinite;
          }
          .hi-pulse-dot-2 {
            animation: hi-pulse-dot 2.4s ease-in-out infinite;
            animation-delay: 0.8s;
          }
          .hi-pulse-dot-3 {
            animation: hi-pulse-dot 2.4s ease-in-out infinite;
            animation-delay: 1.6s;
          }
          .hi-scan-line {
            animation: hi-scan-line 3.2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
          }
          .hi-draw-path {
            stroke-dasharray: 220;
            stroke-dashoffset: 220;
            animation: hi-draw-path 2.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 0.4s;
          }
          .hi-draw-path-2 {
            stroke-dasharray: 120;
            stroke-dashoffset: 120;
            animation: hi-draw-path 1.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 1.2s;
          }
          .hi-fadeup-1 {
            opacity: 0;
            transform: translateY(6px);
            animation: hi-fadeup 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 0.2s;
          }
          .hi-fadeup-2 {
            opacity: 0;
            transform: translateY(6px);
            animation: hi-fadeup 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 0.7s;
          }
          .hi-fadeup-3 {
            opacity: 0;
            transform: translateY(6px);
            animation: hi-fadeup 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 1.2s;
          }
          .hi-fadeup-4 {
            opacity: 0;
            transform: translateY(6px);
            animation: hi-fadeup 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 1.7s;
          }
          .hi-orbit {
            animation: hi-orbit 12s linear infinite;
            transform-origin: 200px 130px;
          }
          .hi-orbit-2 {
            animation: hi-orbit 18s linear infinite reverse;
            transform-origin: 200px 130px;
          }
        }

        @keyframes hi-float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }
        @keyframes hi-pulse-dot {
          0%, 100% { opacity: 0.35; r: 3; }
          50% { opacity: 1; r: 4.5; }
        }
        @keyframes hi-scan-line {
          0% { transform: translateY(0px); opacity: 0.7; }
          45% { opacity: 0.9; }
          100% { transform: translateY(56px); opacity: 0; }
        }
        @keyframes hi-draw-path {
          to { stroke-dashoffset: 0; }
        }
        @keyframes hi-fadeup {
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes hi-orbit {
          from { transform: rotate(0deg) translateX(62px) rotate(0deg); }
          to { transform: rotate(360deg) translateX(62px) rotate(-360deg); }
        }

        .hi-dot-mint { fill: #5de4c7; }
        .hi-dot-blue { fill: #79aeda; }
        .hi-dot-warm { fill: #d2a15f; }

        .hi-card-bg {
          fill: rgba(255, 255, 255, 0.72);
          stroke: rgba(15, 23, 42, 0.07);
        }
        [data-theme="dark"] .hi-card-bg {
          fill: rgba(23, 30, 37, 0.82);
          stroke: rgba(148, 163, 184, 0.1);
        }

        .hi-card-bg-muted {
          fill: rgba(244, 239, 231, 0.7);
          stroke: rgba(15, 23, 42, 0.05);
        }
        [data-theme="dark"] .hi-card-bg-muted {
          fill: rgba(31, 39, 47, 0.82);
          stroke: rgba(148, 163, 184, 0.08);
        }

        .hi-line-base {
          stroke: rgba(15, 23, 42, 0.1);
        }
        [data-theme="dark"] .hi-line-base {
          stroke: rgba(148, 163, 184, 0.14);
        }

        .hi-line-mint {
          stroke: #5de4c7;
        }
        .hi-line-blue {
          stroke: #79aeda;
        }

        .hi-text-primary { fill: #17212b; }
        [data-theme="dark"] .hi-text-primary { fill: #f3f5f7; }

        .hi-text-muted { fill: #8a95a1; }
        [data-theme="dark"] .hi-text-muted { fill: #82909d; }

        .hi-grid-line {
          stroke: rgba(15, 23, 42, 0.04);
        }
        [data-theme="dark"] .hi-grid-line {
          stroke: rgba(148, 163, 184, 0.06);
        }

        .hi-glow-mint {
          fill: rgba(93, 228, 199, 0.18);
        }
        [data-theme="dark"] .hi-glow-mint {
          fill: rgba(93, 228, 199, 0.22);
        }

        .hi-glow-blue {
          fill: rgba(121, 174, 218, 0.14);
        }
        [data-theme="dark"] .hi-glow-blue {
          fill: rgba(121, 174, 218, 0.2);
        }

        .hi-bg-node {
          fill: rgba(255, 255, 255, 0.9);
          stroke: rgba(15, 23, 42, 0.08);
        }
        [data-theme="dark"] .hi-bg-node {
          fill: rgba(19, 24, 31, 0.92);
          stroke: rgba(148, 163, 184, 0.12);
        }

        .hi-bar-track {
          fill: rgba(15, 23, 42, 0.05);
        }
        [data-theme="dark"] .hi-bar-track {
          fill: rgba(148, 163, 184, 0.08);
        }
`;

export function HeroIllustration({ className }: { className?: string }) {
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: HI_STYLES }} />

      <svg
        className={className}
        viewBox="0 0 400 260"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        role="img"
      >
        <defs>
          <radialGradient id="hi-glow-a" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#5de4c7" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#5de4c7" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="hi-glow-b" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#79aeda" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#79aeda" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="hi-grad-mint" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#5de4c7" />
            <stop offset="100%" stopColor="#4fb8af" />
          </linearGradient>
          <linearGradient id="hi-grad-blue" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#79aeda" />
            <stop offset="100%" stopColor="#4c8ec4" />
          </linearGradient>
          <linearGradient id="hi-grad-warm" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#d2a15f" />
            <stop offset="100%" stopColor="#b87b32" />
          </linearGradient>
          <filter id="hi-blur-soft" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="18" />
          </filter>
          <filter id="hi-blur-xs" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" />
          </filter>
          <clipPath id="hi-clip-card-main">
            <rect x="60" y="30" width="136" height="176" rx="16" />
          </clipPath>
          <clipPath id="hi-clip-card-side">
            <rect x="220" y="50" width="114" height="152" rx="14" />
          </clipPath>
        </defs>

        {/* ── Ambient glow blobs ── */}
        <ellipse cx="130" cy="130" rx="90" ry="72" fill="url(#hi-glow-a)" filter="url(#hi-blur-soft)" />
        <ellipse cx="290" cy="110" rx="72" ry="60" fill="url(#hi-glow-b)" filter="url(#hi-blur-soft)" />

        {/* ── Background grid ── */}
        {Array.from({ length: 9 }).map((_, i) => (
          <line
            key={`vg-${i}`}
            x1={i * 50}
            y1="0"
            x2={i * 50}
            y2="260"
            className="hi-grid-line"
            strokeWidth="1"
          />
        ))}
        {Array.from({ length: 7 }).map((_, i) => (
          <line
            key={`hg-${i}`}
            x1="0"
            y1={i * 44}
            x2="400"
            y2={i * 44}
            className="hi-grid-line"
            strokeWidth="1"
          />
        ))}

        {/* ══════════════════════════════════════
            CARD A — 입력 문서 (좌측)
        ══════════════════════════════════════ */}
        <g className="hi-float" style={{ transformOrigin: "128px 118px" }}>
          {/* card shadow */}
          <rect
            x="62"
            y="36"
            width="136"
            height="176"
            rx="16"
            fill="rgba(15,23,42,0.08)"
            filter="url(#hi-blur-xs)"
          />
          {/* card body */}
          <rect
            x="60"
            y="30"
            width="136"
            height="176"
            rx="16"
            strokeWidth="1"
            className="hi-card-bg"
          />

          {/* scan line effect */}
          <g clipPath="url(#hi-clip-card-main)">
            <rect
              className="hi-scan-line"
              x="60"
              y="30"
              width="136"
              height="4"
              fill="url(#hi-grad-mint)"
              opacity="0.5"
            />
          </g>

          {/* card header bar */}
          <rect x="72" y="44" width="112" height="6" rx="3" fill="url(#hi-grad-mint)" opacity="0.9" />

          {/* doc lines */}
          <g className="hi-fadeup-1">
            <rect x="72" y="60" width="90" height="5" rx="2.5" className="hi-line-base" strokeWidth="0" style={{ fill: "rgba(15,23,42,0.08)" }} />
            <rect x="72" y="72" width="112" height="5" rx="2.5" className="hi-line-base" strokeWidth="0" style={{ fill: "rgba(15,23,42,0.08)" }} />
            <rect x="72" y="84" width="76" height="5" rx="2.5" className="hi-line-base" strokeWidth="0" style={{ fill: "rgba(15,23,42,0.08)" }} />
          </g>

          {/* code block mock */}
          <g className="hi-fadeup-2">
            <rect x="72" y="100" width="112" height="40" rx="8" className="hi-bar-track" />
            <rect x="80" y="108" width="56" height="4" rx="2" fill="#5de4c7" opacity="0.7" />
            <rect x="80" y="118" width="80" height="4" rx="2" fill="#79aeda" opacity="0.5" />
            <rect x="80" y="128" width="44" height="4" rx="2" fill="#d2a15f" opacity="0.5" />
          </g>

          {/* small tag badges */}
          <g className="hi-fadeup-3">
            <rect x="72" y="152" width="38" height="16" rx="8" fill="rgba(93,228,199,0.15)" stroke="#5de4c7" strokeWidth="0.8" strokeOpacity="0.5" />
            <rect x="116" y="152" width="32" height="16" rx="8" fill="rgba(121,174,218,0.12)" stroke="#79aeda" strokeWidth="0.8" strokeOpacity="0.4" />
            <rect x="72" y="174" width="112" height="5" rx="2.5" style={{ fill: "rgba(15,23,42,0.06)" }} />
            <rect x="72" y="186" width="86" height="5" rx="2.5" style={{ fill: "rgba(15,23,42,0.06)" }} />
          </g>

          {/* INPUT label */}
          <text x="128" y="220" textAnchor="middle" fontSize="8" fontWeight="700" letterSpacing="0.12em" className="hi-text-muted" style={{ textTransform: "uppercase" }}>INPUT</text>
        </g>

        {/* ══════════════════════════════════════
            CONNECTOR — 파싱 → AI 노드
        ══════════════════════════════════════ */}
        <path
          d="M196 118 C210 118, 210 118, 224 118"
          strokeWidth="1.5"
          strokeLinecap="round"
          className="hi-draw-path hi-line-mint"
          fill="none"
          opacity="0.8"
        />
        {/* arrow head */}
        <path d="M221 114.5 L225.5 118 L221 121.5" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="hi-line-mint" fill="none" opacity="0.8" />

        {/* ══════════════════════════════════════
            CARD B — AI 처리 결과 (우측)
        ══════════════════════════════════════ */}
        <g className="hi-float-slow" style={{ transformOrigin: "277px 126px" }}>
          {/* shadow */}
          <rect
            x="222"
            y="56"
            width="114"
            height="152"
            rx="14"
            fill="rgba(15,23,42,0.07)"
            filter="url(#hi-blur-xs)"
          />
          {/* body */}
          <rect
            x="220"
            y="50"
            width="114"
            height="152"
            rx="14"
            strokeWidth="1"
            className="hi-card-bg-muted"
          />

          {/* accent top strip */}
          <rect x="220" y="50" width="114" height="28" rx="14" className="hi-card-bg-muted" />
          <rect x="220" y="64" width="114" height="14" className="hi-card-bg-muted" />
          <rect x="232" y="58" width="60" height="6" rx="3" fill="url(#hi-grad-blue)" opacity="0.85" />

          {/* AI "processing" dots */}
          <g className="hi-fadeup-2">
            <circle cx="244" cy="88" r="3" className="hi-pulse-dot hi-dot-mint" />
            <circle cx="256" cy="88" r="3" className="hi-pulse-dot-2 hi-dot-blue" />
            <circle cx="268" cy="88" r="3" className="hi-pulse-dot-3 hi-dot-warm" />
            <text x="280" y="92" fontSize="7.5" fontWeight="600" className="hi-text-muted">처리 중</text>
          </g>

          {/* progress bars */}
          <g className="hi-fadeup-3">
            <text x="232" y="110" fontSize="7" className="hi-text-muted" fontWeight="600">PRD</text>
            <rect x="252" y="104" width="68" height="6" rx="3" className="hi-bar-track" />
            <rect x="252" y="104" width="58" height="6" rx="3" fill="url(#hi-grad-mint)" opacity="0.85" />

            <text x="232" y="126" fontSize="7" className="hi-text-muted" fontWeight="600">TRD</text>
            <rect x="252" y="120" width="68" height="6" rx="3" className="hi-bar-track" />
            <rect x="252" y="120" width="40" height="6" rx="3" fill="url(#hi-grad-blue)" opacity="0.75" />

            <text x="232" y="142" fontSize="7" className="hi-text-muted" fontWeight="600">WBS</text>
            <rect x="252" y="136" width="68" height="6" rx="3" className="hi-bar-track" />
            <rect x="252" y="136" width="24" height="6" rx="3" fill="url(#hi-grad-warm)" opacity="0.7" />
          </g>

          {/* divider */}
          <line x1="232" y1="156" x2="322" y2="156" strokeWidth="1" className="hi-line-base" strokeOpacity="0.3" />

          {/* checkmark done line */}
          <g className="hi-fadeup-4">
            <circle cx="240" cy="170" r="6" fill="rgba(93,228,199,0.15)" stroke="#5de4c7" strokeWidth="0.8" />
            <path d="M237 170 L239.5 172.5 L243 167.5" stroke="#5de4c7" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            <rect x="252" y="167" width="60" height="5" rx="2.5" style={{ fill: "rgba(15,23,42,0.07)" }} />

            <circle cx="240" cy="186" r="6" fill="rgba(121,174,218,0.12)" stroke="#79aeda" strokeWidth="0.8" />
            <path d="M237 186 L239.5 188.5 L243 183.5" stroke="#79aeda" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            <rect x="252" y="183" width="48" height="5" rx="2.5" style={{ fill: "rgba(15,23,42,0.07)" }} />
          </g>

          <text x="277" y="217" textAnchor="middle" fontSize="8" fontWeight="700" letterSpacing="0.12em" className="hi-text-muted" style={{ textTransform: "uppercase" }}>OUTPUT</text>
        </g>

        {/* ══════════════════════════════════════
            CENTER AI NODE
        ══════════════════════════════════════ */}
        <g style={{ transformOrigin: "200px 118px" }}>
          {/* outer orbit ring */}
          <circle
            cx="200"
            cy="118"
            r="26"
            stroke="rgba(93,228,199,0.18)"
            strokeWidth="1"
            strokeDasharray="4 6"
            fill="none"
          />
          {/* orbiting particle A */}
          <g className="hi-orbit">
            <circle cx="200" cy="118" r="3" fill="#5de4c7" opacity="0.9" />
          </g>
          {/* orbiting particle B */}
          <g className="hi-orbit-2">
            <circle cx="200" cy="118" r="2" fill="#79aeda" opacity="0.7" />
          </g>

          {/* core node */}
          <circle
            cx="200"
            cy="118"
            r="18"
            strokeWidth="1"
            className="hi-bg-node"
            filter="url(#hi-blur-xs)"
          />
          <circle
            cx="200"
            cy="118"
            r="18"
            strokeWidth="1"
            className="hi-bg-node"
          />
          {/* AI spark icon */}
          <path
            d="M200 108 L202.5 115.5 L210 118 L202.5 120.5 L200 128 L197.5 120.5 L190 118 L197.5 115.5 Z"
            fill="url(#hi-grad-mint)"
            opacity="0.95"
          />
        </g>

        {/* ══════════════════════════════════════
            FLOATING MICRO BADGES
        ══════════════════════════════════════ */}
        {/* top-left: "7 Layers" */}
        <g className="hi-fadeup-1" style={{ transformOrigin: "38px 24px" }}>
          <rect x="14" y="14" width="64" height="22" rx="11" className="hi-bg-node" strokeWidth="0.8" />
          <circle cx="26" cy="25" r="4" fill="rgba(93,228,199,0.2)" />
          <circle cx="26" cy="25" r="2" fill="#5de4c7" />
          <text x="35" y="29" fontSize="7.5" fontWeight="700" className="hi-text-primary">7 Layers</text>
        </g>

        {/* bottom-right: "Auto" */}
        <g className="hi-fadeup-2" style={{ transformOrigin: "362px 238px" }}>
          <rect x="330" y="226" width="56" height="22" rx="11" className="hi-bg-node" strokeWidth="0.8" />
          <circle cx="342" cy="237" r="4" fill="rgba(210,161,95,0.2)" />
          <circle cx="342" cy="237" r="2" fill="#d2a15f" />
          <text x="351" y="241" fontSize="7.5" fontWeight="700" className="hi-text-primary">Auto</text>
        </g>

        {/* top-right: "AI" */}
        <g className="hi-fadeup-3" style={{ transformOrigin: "375px 30px" }}>
          <rect x="354" y="18" width="32" height="22" rx="11" className="hi-bg-node" strokeWidth="0.8" />
          <text x="370" y="33" textAnchor="middle" fontSize="8.5" fontWeight="800" letterSpacing="0.05em" className="hi-text-primary">AI</text>
        </g>

        {/* bottom connector line: card A → AI node */}
        <path
          d="M16 245 Q80 245 130 245"
          strokeWidth="1"
          strokeLinecap="round"
          strokeDasharray="3 5"
          className="hi-line-base"
          fill="none"
          opacity="0.4"
        />
      </svg>
    </>
  );
}
