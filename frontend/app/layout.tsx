import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "../styles/globals.css";

const outfit = Outfit({ subsets: ["latin"], weight: ["300", "400", "500", "600", "700", "800"] });

export const metadata: Metadata = {
  title: "Aegis | Agentic Intelligent Learning Assistant",
  description: "Personalized, AI-driven learning paths that adapt to your pace, style, and mastery level. Powered by Google Cloud and Gemini.",
  keywords: "AI tutor, learning assistant, personalized learning, Gemini, Google Cloud",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={outfit.className}>{children}</body>
    </html>
  );
}
