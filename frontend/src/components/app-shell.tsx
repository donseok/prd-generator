"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { ArrowLeft, Layers, MoonStar, SunMedium } from "lucide-react";

function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

type ThemeMode = "light" | "dark";

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
      className="secondary-button !h-11 !rounded-[18px] !px-4 !py-0"
      aria-label="테마 전환"
      title={mounted ? (theme === "light" ? "다크 모드" : "라이트 모드") : "테마 전환"}
    >
      {mounted && theme === "dark" ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      <span>{mounted && theme === "dark" ? "라이트" : "다크"}</span>
    </button>
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
      <div className="pointer-events-none absolute inset-x-0 top-0 z-0 h-72 bg-gradient-to-b from-white/25 to-transparent dark:from-white/5" />
      <div className="relative z-10">{header}</div>
      <main className="page-reveal relative z-10 mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-8 md:px-8 md:py-10">
        {children}
      </main>
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
    <header className="top-bar sticky top-0 z-30 border-b backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-5 py-4 md:flex-row md:items-center md:justify-between md:gap-4 md:px-8">
        <div className="flex min-w-0 items-start gap-3 md:items-center">
          <Link href={href} className="secondary-button !mt-0.5 !h-11 !w-11 !rounded-[16px] !p-0 md:!mt-0" aria-label="뒤로 가기">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[16px] text-white shadow-lg"
            style={{ background: "var(--gradient-brand)" }}
          >
            <Layers className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h1 className="line-clamp-2 text-lg font-bold tracking-[-0.04em] text-slate-900 md:text-xl">{title}</h1>
            {subtitle ? <p className="mt-1 line-clamp-1 text-sm text-slate-500">{subtitle}</p> : null}
          </div>
        </div>
        <div className="flex w-full flex-wrap items-center gap-2 md:w-auto md:justify-end">{action}{<ThemeToggle />}</div>
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
      <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1.18fr)_360px] lg:items-end">
        <div className="space-y-6">
          <span className="hero-kicker">{kicker}</span>
          <h2 className="hero-title">{title}</h2>
          <p className="hero-body">{description}</p>
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        </div>
        {aside ? (
          <div className="surface-muted relative overflow-hidden p-5 md:p-6">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-white/15 to-transparent" />
            <div className="relative">{aside}</div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

export function MetricCard({
  label,
  value,
  note,
  accent = "brand",
}: {
  label: string;
  value: string | number;
  note?: string;
  accent?: "brand" | "warm" | "mint";
}) {
  const accentStyle =
    accent === "warm"
      ? { background: "var(--gradient-warm)" }
      : accent === "mint"
      ? { background: "linear-gradient(135deg, #1f8f7c 0%, #7de3c5 100%)" }
      : { background: "var(--gradient-brand)" };

  return (
    <div className="list-card stagger-in">
      <div className="mb-5 flex items-center justify-between gap-3">
        <span className="data-label">{label}</span>
        <span className="h-2.5 w-14 rounded-full" style={accentStyle} />
      </div>
      <p className="text-[2.2rem] font-black leading-none tracking-[-0.06em] text-slate-900">{value}</p>
      {note ? <p className="mt-3 text-sm leading-6 text-slate-500">{note}</p> : null}
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
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between sm:gap-4">
      <div className="space-y-1">
        <h3 className="section-title">{title}</h3>
        {description ? <p className="section-caption">{description}</p> : null}
      </div>
      {action}
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
