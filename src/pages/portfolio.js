import React from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import styles from "./portfolio.module.css";

const cards = [
  {
    title: "AI/ML Docs",
    description: "Documentation focused on embeddings, LLM integration, and AI workflows.",
    to: "/aiml/intro",
  },
  {
    title: "Docs",
    description: "Task-driven guides, conceptual explainers, and developer onboarding content.",
    to: "/docs/intro",
  },
  {
    title: "APIs",
    description: "API reference samples, OpenAPI structure, and developer experience patterns.",
    to: "/apis/intro",
  },
  {
    title: "Architecture",
    description: "Architecture narratives and diagrams that explain how systems work end-to-end.",
    to: "/architecture/intro",
  },
  {
    title: "Content Strategy",
    description: "Content planning, SEO and GEO-led doc strategy, and technical content systems.",
    to: "/strategy/intro",
  },
];

export default function Portfolio() {
  return (
    <Layout title="Portfolio | Sujatha R" description="Portfolio areas: AI/ML Docs, Docs, APIs, Architecture, Content Strategy">
      <main className={styles.page}>
        <div className="container">
          <div className={styles.header}>
            <h1 className={styles.title}>Portfolio</h1>
            <p className={styles.subtitle}>
              Browse by category. Each section highlights representative work and writing patterns.
            </p>
          </div>

          <div className={styles.grid}>
            {cards.map((c) => (
              <Link key={c.title} className={styles.card} to={c.to}>
                <div className={styles.cardInner}>
                  <h2 className={styles.cardTitle}>{c.title}</h2>
                  <p className={styles.cardDesc}>{c.description}</p>
                  <span className={styles.cardCta}>Open →</span>
                </div>
              </Link>
            ))}
          </div>

          <div className={styles.backRow}>
            <Link to="/" className="button button--secondary">
              ← Back to Home
            </Link>
          </div>
        </div>
      </main>
    </Layout>
  );
}