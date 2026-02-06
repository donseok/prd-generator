import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "문서 자동 생성시스템",
  description: "다양한 입력 형식을 표준 PRD로 변환하는 AI 파이프라인",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="bg-slate-900 text-white min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
