import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ui/theme-provider";
import ErrorBoundary from "@/components/error-boundary";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "VOXY - AI Multi-Agent Assistant",
  description: "Intelligent multi-agent system for translations, corrections, weather, calculations and more.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ErrorBoundary>
          <ThemeProvider
            defaultTheme="system"
            storageKey="voxy-theme"
          >
            {children}
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
