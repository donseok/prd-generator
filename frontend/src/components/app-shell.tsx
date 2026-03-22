"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ArrowLeft, FileText, FolderKanban, Home, MoonStar, Sparkles, SunMedium, History } from "lucide-react";

function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

type ThemeMode = "light" | "dark";

/* -------------------------------------------------------------------------- */
/*  Hero Illustration – Premium isometric document-generation network         */
/* -------------------------------------------------------------------------- */

function HeroIllustration() {
  return (
    <svg
      viewBox="0 0 320 240"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full h-auto animate-float"
      aria-hidden="true"
    >
      <defs>
        {/* Core gradients */}
        <linearGradient id="grad-indigo" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366F1" />
          <stop offset="100%" stopColor="#8B5CF6" />
        </linearGradient>
        <linearGradient id="grad-violet" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#8B5CF6" />
          <stop offset="100%" stopColor="#A78BFA" />
        </linearGradient>
        <linearGradient id="grad-cyan" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#06B6D4" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
        <linearGradient id="grad-emerald" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#10B981" />
          <stop offset="100%" stopColor="#34D399" />
        </linearGradient>
        <linearGradient id="grad-amber" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#FBBF24" />
        </linearGradient>
        <linearGradient id="grad-rose" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F43F5E" />
          <stop offset="100%" stopColor="#FB7185" />
        </linearGradient>

        {/* Glow effects */}
        <radialGradient id="glow-indigo" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#6366F1" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="glow-cyan" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#06B6D4" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="glow-emerald" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#10B981" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
        </radialGradient>

        {/* Document shadow filter */}
        <filter id="doc-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#6366F1" floodOpacity="0.15" />
        </filter>
        <filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* === Background ambient glow fields === */}
      <ellipse cx="160" cy="120" rx="120" ry="90" fill="url(#glow-indigo)" />
      <ellipse cx="80" cy="80" rx="60" ry="50" fill="url(#glow-cyan)" />
      <ellipse cx="240" cy="160" rx="55" ry="45" fill="url(#glow-emerald)" />

      {/* === Flowing connection lines (animated dashes) === */}
      {/* Central hub to PRD doc */}
      <path d="M160 120 C130 100, 100 85, 78 72" stroke="url(#grad-indigo)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" strokeDasharray="4 3">
        <animate attributeName="stroke-dashoffset" values="0;-14" dur="2s" repeatCount="indefinite" />
      </path>
      {/* Central hub to TRD doc */}
      <path d="M160 120 C190 95, 220 80, 242 68" stroke="url(#grad-cyan)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" strokeDasharray="4 3">
        <animate attributeName="stroke-dashoffset" values="0;-14" dur="2.3s" repeatCount="indefinite" />
      </path>
      {/* Central hub to WBS doc */}
      <path d="M160 120 C140 145, 110 165, 82 178" stroke="url(#grad-emerald)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" strokeDasharray="4 3">
        <animate attributeName="stroke-dashoffset" values="0;-14" dur="2.6s" repeatCount="indefinite" />
      </path>
      {/* Central hub to Proposal doc */}
      <path d="M160 120 C185 150, 215 170, 245 178" stroke="url(#grad-violet)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" strokeDasharray="4 3">
        <animate attributeName="stroke-dashoffset" values="0;-14" dur="2.1s" repeatCount="indefinite" />
      </path>
      {/* Cross connections */}
      <path d="M78 72 C100 120, 60 155, 82 178" stroke="#8B5CF6" strokeWidth="0.8" strokeLinecap="round" opacity="0.15" strokeDasharray="3 4">
        <animate attributeName="stroke-dashoffset" values="0;-14" dur="3s" repeatCount="indefinite" />
      </path>
      <path d="M242 68 C260 120, 260 155, 245 178" stroke="#06B6D4" strokeWidth="0.8" strokeLinecap="round" opacity="0.15" strokeDasharray="3 4">
        <animate attributeName="stroke-dashoffset" values="0;-14" dur="3.2s" repeatCount="indefinite" />
      </path>

      {/* === Central AI processing hub === */}
      <g filter="url(#node-glow)">
        {/* Outer ring pulse */}
        <circle cx="160" cy="120" r="28" fill="none" stroke="url(#grad-indigo)" strokeWidth="1" opacity="0.3">
          <animate attributeName="r" values="28;34;28" dur="3s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.3;0.1;0.3" dur="3s" repeatCount="indefinite" />
        </circle>
        {/* Main hub circle */}
        <circle cx="160" cy="120" r="22" fill="url(#grad-indigo)" opacity="0.95" />
        {/* Inner ring */}
        <circle cx="160" cy="120" r="16" fill="none" stroke="white" strokeWidth="0.8" opacity="0.3" />
        {/* AI sparkle icon inside hub */}
        <path d="M160 110 L162 117 L169 118 L163 121 L165 128 L160 123 L155 128 L157 121 L151 118 L158 117 Z" fill="white" opacity="0.9" />
      </g>

      {/* === PRD Document (top-left) – Indigo === */}
      <g filter="url(#doc-shadow)">
        <g transform="translate(48, 38)">
          {/* Document body */}
          <rect width="56" height="68" rx="8" fill="white" opacity="0.95" />
          <rect width="56" height="68" rx="8" fill="url(#grad-indigo)" opacity="0.08" />
          <rect width="56" height="68" rx="8" fill="none" stroke="url(#grad-indigo)" strokeWidth="1" opacity="0.3" />
          {/* Header bar */}
          <rect x="8" y="8" width="40" height="4" rx="2" fill="url(#grad-indigo)" opacity="0.7" />
          {/* Content lines */}
          <rect x="8" y="18" width="34" height="2.5" rx="1.25" fill="#6366F1" opacity="0.2" />
          <rect x="8" y="24" width="40" height="2" rx="1" fill="#6366F1" opacity="0.12" />
          <rect x="8" y="29" width="28" height="2" rx="1" fill="#6366F1" opacity="0.12" />
          <rect x="8" y="34" width="36" height="2" rx="1" fill="#6366F1" opacity="0.12" />
          {/* Mini chart */}
          <rect x="8" y="42" width="8" height="16" rx="2" fill="url(#grad-indigo)" opacity="0.2" />
          <rect x="19" y="46" width="8" height="12" rx="2" fill="url(#grad-indigo)" opacity="0.15" />
          <rect x="30" y="44" width="8" height="14" rx="2" fill="url(#grad-indigo)" opacity="0.25" />
          {/* PRD label */}
          <text x="28" y="66" textAnchor="middle" fontSize="5.5" fontWeight="700" fill="#6366F1" opacity="0.6" fontFamily="system-ui">PRD</text>
        </g>
      </g>

      {/* === TRD Document (top-right) – Cyan === */}
      <g filter="url(#doc-shadow)">
        <g transform="translate(218, 34)">
          <rect width="56" height="68" rx="8" fill="white" opacity="0.95" />
          <rect width="56" height="68" rx="8" fill="url(#grad-cyan)" opacity="0.06" />
          <rect width="56" height="68" rx="8" fill="none" stroke="url(#grad-cyan)" strokeWidth="1" opacity="0.3" />
          {/* Header */}
          <rect x="8" y="8" width="40" height="4" rx="2" fill="url(#grad-cyan)" opacity="0.7" />
          {/* Architecture diagram mini */}
          <rect x="8" y="18" width="16" height="12" rx="3" fill="#06B6D4" opacity="0.15" />
          <rect x="28" y="18" width="16" height="12" rx="3" fill="#06B6D4" opacity="0.15" />
          <line x1="24" y1="24" x2="28" y2="24" stroke="#06B6D4" strokeWidth="1" opacity="0.3" />
          {/* Content lines */}
          <rect x="8" y="36" width="40" height="2" rx="1" fill="#06B6D4" opacity="0.12" />
          <rect x="8" y="41" width="32" height="2" rx="1" fill="#06B6D4" opacity="0.12" />
          <rect x="8" y="46" width="38" height="2" rx="1" fill="#06B6D4" opacity="0.12" />
          {/* API endpoint indicators */}
          <rect x="8" y="54" width="18" height="5" rx="2.5" fill="url(#grad-cyan)" opacity="0.2" />
          <rect x="29" y="54" width="18" height="5" rx="2.5" fill="url(#grad-cyan)" opacity="0.15" />
          {/* TRD label */}
          <text x="28" y="66" textAnchor="middle" fontSize="5.5" fontWeight="700" fill="#06B6D4" opacity="0.6" fontFamily="system-ui">TRD</text>
        </g>
      </g>

      {/* === WBS Document (bottom-left) – Emerald === */}
      <g filter="url(#doc-shadow)">
        <g transform="translate(48, 148)">
          <rect width="56" height="68" rx="8" fill="white" opacity="0.95" />
          <rect width="56" height="68" rx="8" fill="url(#grad-emerald)" opacity="0.06" />
          <rect width="56" height="68" rx="8" fill="none" stroke="url(#grad-emerald)" strokeWidth="1" opacity="0.3" />
          {/* Header */}
          <rect x="8" y="8" width="40" height="4" rx="2" fill="url(#grad-emerald)" opacity="0.7" />
          {/* Gantt-like bars */}
          <rect x="8" y="18" width="30" height="4" rx="2" fill="url(#grad-emerald)" opacity="0.25" />
          <rect x="14" y="25" width="24" height="4" rx="2" fill="url(#grad-emerald)" opacity="0.18" />
          <rect x="10" y="32" width="32" height="4" rx="2" fill="url(#grad-emerald)" opacity="0.22" />
          <rect x="16" y="39" width="20" height="4" rx="2" fill="url(#grad-emerald)" opacity="0.15" />
          {/* Checkmarks */}
          <path d="M42 19 L44 21 L48 17" stroke="#10B981" strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.5" />
          <path d="M42 26 L44 28 L48 24" stroke="#10B981" strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.5" />
          <circle cx="45" cy="34" r="2.5" fill="none" stroke="#10B981" strokeWidth="0.8" opacity="0.3" />
          {/* WBS label */}
          <text x="28" y="60" textAnchor="middle" fontSize="5.5" fontWeight="700" fill="#10B981" opacity="0.6" fontFamily="system-ui">WBS</text>
        </g>
      </g>

      {/* === Proposal Document (bottom-right) – Violet === */}
      <g filter="url(#doc-shadow)">
        <g transform="translate(218, 148)">
          <rect width="56" height="68" rx="8" fill="white" opacity="0.95" />
          <rect width="56" height="68" rx="8" fill="url(#grad-violet)" opacity="0.06" />
          <rect width="56" height="68" rx="8" fill="none" stroke="url(#grad-violet)" strokeWidth="1" opacity="0.3" />
          {/* Header */}
          <rect x="8" y="8" width="40" height="4" rx="2" fill="url(#grad-violet)" opacity="0.7" />
          {/* Presentation-style content */}
          <rect x="8" y="18" width="40" height="20" rx="4" fill="#8B5CF6" opacity="0.08" />
          <rect x="12" y="22" width="24" height="2.5" rx="1.25" fill="#8B5CF6" opacity="0.25" />
          <rect x="12" y="27" width="32" height="2" rx="1" fill="#8B5CF6" opacity="0.15" />
          <rect x="12" y="32" width="18" height="2" rx="1" fill="#8B5CF6" opacity="0.12" />
          {/* Dollar/budget indicator */}
          <rect x="8" y="44" width="18" height="14" rx="3" fill="url(#grad-violet)" opacity="0.1" />
          <text x="17" y="54" textAnchor="middle" fontSize="8" fontWeight="700" fill="#8B5CF6" opacity="0.35" fontFamily="system-ui">$</text>
          {/* Timeline dots */}
          <circle cx="33" cy="47" r="2" fill="#8B5CF6" opacity="0.25" />
          <circle cx="39" cy="47" r="2" fill="#8B5CF6" opacity="0.2" />
          <circle cx="45" cy="47" r="2" fill="#8B5CF6" opacity="0.15" />
          <line x1="33" y1="47" x2="45" y2="47" stroke="#8B5CF6" strokeWidth="0.6" opacity="0.15" />
          {/* Proposal label */}
          <text x="28" y="66" textAnchor="middle" fontSize="4.5" fontWeight="700" fill="#8B5CF6" opacity="0.6" fontFamily="system-ui">PROPOSAL</text>
        </g>
      </g>

      {/* === Floating connection nodes (data flow particles) === */}
      {/* Node along PRD path */}
      <circle r="3" fill="url(#grad-indigo)" opacity="0.8">
        <animateMotion dur="2s" repeatCount="indefinite" path="M160 120 C130 100, 100 85, 78 72" />
      </circle>
      {/* Node along TRD path */}
      <circle r="3" fill="url(#grad-cyan)" opacity="0.8">
        <animateMotion dur="2.3s" repeatCount="indefinite" path="M160 120 C190 95, 220 80, 242 68" />
      </circle>
      {/* Node along WBS path */}
      <circle r="3" fill="url(#grad-emerald)" opacity="0.8">
        <animateMotion dur="2.6s" repeatCount="indefinite" path="M160 120 C140 145, 110 165, 82 178" />
      </circle>
      {/* Node along Proposal path */}
      <circle r="3" fill="url(#grad-violet)" opacity="0.8">
        <animateMotion dur="2.1s" repeatCount="indefinite" path="M160 120 C185 150, 215 170, 245 178" />
      </circle>

      {/* === Floating ambient particles === */}
      {/* Particle cluster - top */}
      <circle cx="140" cy="20" r="2" fill="#6366F1" opacity="0.4">
        <animate attributeName="cy" values="20;14;20" dur="4s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.4;0.15;0.4" dur="4s" repeatCount="indefinite" />
      </circle>
      <circle cx="185" cy="16" r="1.5" fill="#06B6D4" opacity="0.35">
        <animate attributeName="cy" values="16;10;16" dur="3.5s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.35;0.1;0.35" dur="3.5s" repeatCount="indefinite" />
      </circle>
      <circle cx="120" cy="28" r="1.2" fill="#8B5CF6" opacity="0.3">
        <animate attributeName="cy" values="28;22;28" dur="4.2s" repeatCount="indefinite" />
      </circle>

      {/* Particle cluster - bottom */}
      <circle cx="160" cy="228" r="1.8" fill="#10B981" opacity="0.35">
        <animate attributeName="cy" values="228;222;228" dur="3.8s" repeatCount="indefinite" />
      </circle>
      <circle cx="200" cy="232" r="1.2" fill="#8B5CF6" opacity="0.3">
        <animate attributeName="cy" values="232;226;232" dur="4.5s" repeatCount="indefinite" />
      </circle>

      {/* Particle cluster - sides */}
      <circle cx="16" cy="110" r="1.8" fill="#06B6D4" opacity="0.3">
        <animate attributeName="cx" values="16;12;16" dur="3.6s" repeatCount="indefinite" />
      </circle>
      <circle cx="305" cy="130" r="1.5" fill="#6366F1" opacity="0.25">
        <animate attributeName="cx" values="305;309;305" dur="4.1s" repeatCount="indefinite" />
      </circle>
      <circle cx="20" cy="170" r="1.2" fill="#10B981" opacity="0.2">
        <animate attributeName="cx" values="20;15;20" dur="3.9s" repeatCount="indefinite" />
      </circle>
      <circle cx="300" cy="80" r="2" fill="#F59E0B" opacity="0.2">
        <animate attributeName="cx" values="300;304;300" dur="4.4s" repeatCount="indefinite" />
      </circle>

      {/* === Decorative elements === */}
      {/* Hexagon top-left */}
      <polygon points="30,55 36,51 42,55 42,63 36,67 30,63" fill="none" stroke="#6366F1" strokeWidth="0.6" opacity="0.15">
        <animate attributeName="opacity" values="0.15;0.08;0.15" dur="5s" repeatCount="indefinite" />
      </polygon>

      {/* Hexagon bottom-right */}
      <polygon points="280,180 286,176 292,180 292,188 286,192 280,188" fill="none" stroke="#06B6D4" strokeWidth="0.6" opacity="0.12">
        <animate attributeName="opacity" values="0.12;0.06;0.12" dur="4.5s" repeatCount="indefinite" />
      </polygon>

      {/* Diamond decorations */}
      <rect x="-3" y="-3" width="6" height="6" rx="1" fill="#8B5CF6" opacity="0.12" transform="translate(12, 40) rotate(45)" />
      <rect x="-2.5" y="-2.5" width="5" height="5" rx="1" fill="#06B6D4" opacity="0.1" transform="translate(308, 170) rotate(45)" />
      <rect x="-2" y="-2" width="4" height="4" rx="0.5" fill="#10B981" opacity="0.15" transform="translate(160, 8) rotate(45)" />

      {/* Plus signs */}
      <g transform="translate(298, 40)" opacity="0.15">
        <rect x="-1" y="-4.5" width="2" height="9" rx="1" fill="#6366F1" />
        <rect x="-4.5" y="-1" width="9" height="2" rx="1" fill="#6366F1" />
      </g>
      <g transform="translate(22, 210)" opacity="0.12">
        <rect x="-1" y="-4" width="2" height="8" rx="1" fill="#8B5CF6" />
        <rect x="-4" y="-1" width="8" height="2" rx="1" fill="#8B5CF6" />
      </g>
      <g transform="translate(140, 232)" opacity="0.1">
        <rect x="-0.8" y="-3" width="1.6" height="6" rx="0.8" fill="#06B6D4" />
        <rect x="-3" y="-0.8" width="6" height="1.6" rx="0.8" fill="#06B6D4" />
      </g>

      {/* Orbit rings around hub */}
      <ellipse cx="160" cy="120" rx="50" ry="38" fill="none" stroke="#6366F1" strokeWidth="0.4" opacity="0.08" strokeDasharray="2 4" transform="rotate(-15 160 120)">
        <animate attributeName="stroke-dashoffset" values="0;12" dur="8s" repeatCount="indefinite" />
      </ellipse>
      <ellipse cx="160" cy="120" rx="70" ry="52" fill="none" stroke="#8B5CF6" strokeWidth="0.3" opacity="0.06" strokeDasharray="3 5" transform="rotate(10 160 120)">
        <animate attributeName="stroke-dashoffset" values="0;-16" dur="10s" repeatCount="indefinite" />
      </ellipse>
    </svg>
  );
}

/* -------------------------------------------------------------------------- */
/*  Theme Toggle                                                              */
/* -------------------------------------------------------------------------- */

function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeMode>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("theme-mode");
    const nextTheme: ThemeMode = stored === "dark" ? "dark" : "light";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
    setMounted(true);
  }, []);

  function toggleTheme() {
    const nextTheme: ThemeMode = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem("theme-mode", nextTheme);
  }

  return (
    <button
      onClick={toggleTheme}
      className="secondary-button !h-10 !rounded-xl !px-3 !py-0"
      aria-label="테마 전환"
      title={mounted ? (theme === "light" ? "다크 모드" : "라이트 모드") : "테마 전환"}
    >
      {mounted && theme === "dark" ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      <span>{mounted && theme === "dark" ? "라이트" : "다크"}</span>
    </button>
  );
}

/* -------------------------------------------------------------------------- */
/*  AppShell                                                                  */
/* -------------------------------------------------------------------------- */

const NAV_ITEMS = [
  { href: "/", label: "대시보드", icon: Home },
  { href: "/projects", label: "프로젝트", icon: FolderKanban },
  { href: "/upload", label: "새 문서", icon: Sparkles },
  { href: "/history", label: "PRD 아카이브", icon: History },
];

function GlobalNav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-[var(--line-soft)] bg-[var(--bg-panel)] backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-1 px-5 md:px-8">
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors",
                active
                  ? "border-[#6366F1] text-[#6366F1]"
                  : "border-transparent text-slate-500 hover:border-[#6366F1]/30 hover:text-[#6366F1]/70"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
        <div className="ml-auto py-2">
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}

export function AppShell({
  children,
  header,
  className,
}: {
  children: ReactNode;
  header?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("app-shell app-grid", className)}>
      <GlobalNav />
      <div className="relative z-10">{header}</div>
      <main className="page-reveal relative z-10 mx-auto flex w-full max-w-6xl flex-col gap-8 px-5 py-8 md:px-8 md:py-10">
        {children}
      </main>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  TopBar                                                                    */
/* -------------------------------------------------------------------------- */

export function TopBar({
  title,
  subtitle,
  href = "/",
  action,
}: {
  title: string;
  subtitle?: string;
  href?: string;
  action?: ReactNode;
}) {
  return (
    <header className="top-bar sticky top-0 z-30 border-b">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-5 py-4 md:flex-row md:items-center md:justify-between md:px-8">
        <div className="flex min-w-0 items-start gap-3 md:items-center">
          <Link href={href} className="secondary-button !h-9 !w-9 !rounded-xl !p-0" aria-label="뒤로 가기">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-[#6366F1]/10 bg-[#6366F1]/5 text-[#6366F1]">
            <FileText className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <h1 className="line-clamp-2 text-lg font-semibold tracking-[-0.03em] text-slate-900 md:text-xl">{title}</h1>
            {subtitle ? <p className="mt-0.5 line-clamp-1 text-sm text-slate-500">{subtitle}</p> : null}
          </div>
        </div>
        <div className="flex w-full flex-wrap items-center gap-2 md:w-auto md:justify-end">
          <ThemeToggle />
          {action}
        </div>
      </div>
    </header>
  );
}

/* -------------------------------------------------------------------------- */
/*  HeroPanel                                                                 */
/* -------------------------------------------------------------------------- */

export function HeroPanel({
  kicker,
  title,
  description,
  actions,
  aside,
}: {
  kicker: string;
  title: string;
  description: string;
  actions?: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <section className="hero-panel">
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_320px] lg:items-start">
        <div className="space-y-5">
          <span className="hero-kicker">{kicker}</span>
          <h2 className="hero-title">{title}</h2>
          <p className="hero-body">{description}</p>
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        </div>
        {aside ? (
          <div className="space-y-5">
            <div className="flex justify-center">
              <HeroIllustration />
            </div>
            <div className="surface-muted p-5 md:p-6">{aside}</div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  MetricCard                                                                */
/* -------------------------------------------------------------------------- */

const ACCENT_COLORS: Record<string, string> = {
  brand: "#6366F1",
  warm: "#F59E0B",
  mint: "#10B981",
};

export function MetricCard({
  label,
  value,
  note,
  accent,
}: {
  label: string;
  value: string | number;
  note?: string;
  accent?: "brand" | "warm" | "mint";
}) {
  const borderColor = accent ? ACCENT_COLORS[accent] : "var(--line-strong)";

  return (
    <div
      className="list-card stagger-in"
      style={{ borderLeft: `3px solid ${borderColor}` }}
    >
      <div className="mb-3">
        <span className="data-label">{label}</span>
      </div>
      <p className="text-[1.75rem] font-extrabold leading-none tracking-[-0.04em] text-slate-900">{value}</p>
      {note ? <p className="mt-2.5 text-sm leading-6 text-slate-500">{note}</p> : null}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  SectionHeader                                                             */
/* -------------------------------------------------------------------------- */

export function SectionHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="space-y-1">
        <h3 className="section-title">{title}</h3>
        {description ? <p className="section-caption">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Utilities                                                                 */
/* -------------------------------------------------------------------------- */

export function formatDate(value?: string, options?: Intl.DateTimeFormatOptions) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR", options);
}

export function scoreBadge(score: number) {
  const percent = Math.round(score * 100);
  if (percent >= 80) {
    return { label: `${percent}%`, className: "bg-emerald-100 text-emerald-700 dark-badge" };
  }
  if (percent >= 60) {
    return { label: `${percent}%`, className: "bg-amber-100 text-amber-700 dark-badge" };
  }
  return { label: `${percent}%`, className: "bg-rose-100 text-rose-700 dark-badge" };
}
