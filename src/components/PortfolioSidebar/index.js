import React from "react";
import Link from "@docusaurus/Link";
import styles from "./styles.module.css";

const navItems = [
  { to: "/", label: "Home" },
  { to: "/aiml/intro", label: "AI/ML Docs" },
  { to: "/docs/intro", label: "Docs" },
  { to: "/apis/intro", label: "APIs" },
  { to: "/architecture/intro", label: "Architecture" },
  { to: "/strategy/intro", label: "Content Strategy" },
  { to: "/experience", label: "Experience" },
  {
    href: "https://github.com/rsujathacse/sujatha-portfolio",
    label: "GitHub",
  },
];

export default function PortfolioSidebar({ title = "Home" }) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.title}>{title.toUpperCase()}</div>

      <nav className={styles.nav}>
        {navItems.map((item) =>
          item.href ? (
            <a
              key={item.label}
              href={item.href}
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              {item.label}
            </a>
          ) : (
            <Link key={item.label} to={item.to} className={styles.link}>
              {item.label}
            </Link>
          )
        )}
      </nav>
    </aside>
  );
}