"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import {
  ArrowLeft,
  FileText,
  FolderKanban,
  History,
  Home,
  MoonStar,
  Sparkles,
  SunMedium,
} from "lucide-react";

function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

type ThemeMode = "light" | "dark";

function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span className="brand-mark-stripe" />
      <span className="brand-mark-core" />
    </div>
  );
}

function QuietFigure() {
  return (
    <div className="quiet-figure" aria-hidden="true">
      <div className="quiet-sheet quiet-sheet-back" />
      <div className="quiet-sheet quiet-sheet-mid" />
      <div className="quiet-sheet quiet-sheet-front">
        <span className="quiet-line quiet-line-long" />
        <span className="quiet-line quiet-line-mid" />
        <span className="quiet-line quiet-line-short" />
      </div>
    </div>
  );
}

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

  if (!mounted) return <div className="w-9 h-9" />; // placeholder to prevent layout shift

  return (
    <button
      onClick={toggleTheme}
      className="secondary-button secondary-button-compact"
      aria-label="테마 전환"
      title={theme === "light" ? "다크 모드" : "라이트 모드"}
    >
      {theme === "dark" ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      <span>{theme === "dark" ? "라이트" : "다크"}</span>
    </button>
  );
}

const NAV_ITEMS = [
  { href: "/", label: "대시보드", icon: Home },
  { href: "/projects", label: "프로젝트", icon: FolderKanban },
  { href: "/upload", label: "새 문서", icon: Sparkles },
  { href: "/history", label: "아카이브", icon: History },
];

function GlobalNav() {
  const pathname = usePathname() ?? "";

  return (
    <header className="shell-header">
      <div className="shell-header-inner">
        <Link href="/" className="shell-brand">
          <BrandMark />
          <div className="shell-brand-copy">
            <span className="shell-brand-title">D&apos;Maker</span>
            <span className="shell-brand-subtitle">AI 문서 자동화</span>
          </div>
        </Link>

        <nav className="shell-nav" aria-label="주요 메뉴">
          {NAV_ITEMS.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn("nav-link", active && "nav-link-active")}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="shell-actions">
          <ThemeToggle />
        </div>
      </div>
    </header>
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
    <div className={cn("app-shell", className)}>
      <div className="app-ambient app-ambient-left" aria-hidden="true" />
      <div className="app-ambient app-ambient-right" aria-hidden="true" />
      <GlobalNav />
      {header ? <div className="relative z-10">{header}</div> : null}
      <main className="page-reveal app-main">{children}</main>
    </div>
  );
}

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
    <header className="page-topbar">
      <div className="page-topbar-inner">
        <div className="page-topbar-copy">
          <Link href={href} className="secondary-button secondary-button-icon" aria-label="뒤로 가기">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="page-topbar-meta">
            <div className="page-topbar-label">
              <FileText className="h-4 w-4" />
              문서 워크스페이스
            </div>
            <h1 className="page-topbar-title">{title}</h1>
            {subtitle ? <p className="page-topbar-subtitle">{subtitle}</p> : null}
          </div>
        </div>
        {action ? <div className="page-topbar-actions">{action}</div> : null}
      </div>
    </header>
  );
}

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
      <div className={cn("hero-layout", aside ? "hero-layout-with-aside" : undefined)}>
        <div className="hero-copy">
          <span className="hero-kicker">{kicker}</span>
          <h2 className="hero-title">{title}</h2>
          <p className="hero-body">{description}</p>
          {actions ? <div className="hero-actions">{actions}</div> : null}
        </div>
        {aside ? (
          <aside className="hero-side">
            <QuietFigure />
            <div className="surface-muted hero-side-card">{aside}</div>
          </aside>
        ) : null}
      </div>
    </section>
  );
}

const ACCENT_TONES: Record<string, string> = {
  brand: "var(--accent-strong)",
  warm: "var(--accent-warm)",
  mint: "var(--accent)",
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
  return (
    <div className="metric-card stagger-in">
      <div className="metric-card-header">
        <span
          className="metric-card-dot"
          style={{ backgroundColor: accent ? ACCENT_TONES[accent] : "var(--line-strong)" }}
        />
        <span className="data-label">{label}</span>
      </div>
      <p className="metric-card-value">{value}</p>
      {note ? <p className="metric-card-note">{note}</p> : null}
    </div>
  );
}

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
    <div className="section-header">
      <div className="section-heading">
        <h3 className="section-title">{title}</h3>
        {description ? <p className="section-caption">{description}</p> : null}
      </div>
      {action ? <div className="section-action">{action}</div> : null}
    </div>
  );
}

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
