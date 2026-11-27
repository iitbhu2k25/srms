"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Droplets } from "lucide-react";
import { NAV_GROUPS, PAGES } from "./nav";

export default function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const isActive = (href: string) => (href === "/" ? path === "/" : path.startsWith(href));
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-title"><Droplets size={20} color="#22d3ee" /> SRMS</div>
          <div className="brand-sub">Smart River Monitoring System<br />Varuna River Basin</div>
        </div>
        <nav className="nav">
          {NAV_GROUPS.map((group) => (
            <div key={group}>
              <div className="nav-section">{group}</div>
              {PAGES.filter((p) => p.group === group).map(({ href, label, icon: Icon }) => (
                <Link key={href} href={href} className={isActive(href) ? "active" : ""}>
                  <Icon size={16} /> {label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot">SLCR · IIT (BHU) Varanasi<br />v0.2 · dummy data</div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
