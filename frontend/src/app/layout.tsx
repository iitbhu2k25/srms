import type { Metadata } from "next";
import Shell from "@/components/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "SRMS — Smart River Monitoring System | Varuna",
  description: "Centralized digital platform for the Smart River Monitoring System, Varuna River Basin (SLCR, IIT BHU).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
