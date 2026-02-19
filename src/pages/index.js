import React from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import styles from "./index.module.css";

export default function Home() {
  return (
    <Layout
      title="Sujatha R"
      description="Senior Technical Writer focusing on cloud, APIs, and AI/ML workflows."
    >
      <main>

        {/* HERO — Clean, neutral */}
        <section className={styles.hero}>
          <div className={styles.heroInner}>
            <h1 className={styles.heroTitle}>Sujatha R</h1>

            <p className={styles.heroKicker}>
              10+ years crafting complex cloud and AI systems into clear, developer-ready docs.
            </p>

            <p className={styles.heroBody}>
              I’m a Senior Technical Writer building developer-first documentation across
              cloud, APIs, and AI/ML workflows. I partner with engineering and product teams to craft clear, task-driven
              docs: reference guides, concept explainers, and architecture decoders to help
              users succeed faster.
            </p>

            <div className={styles.heroCtas}>
              <Link
                className={`button button--primary button--lg ${styles.primaryBtn}`}
                to="/portfolio"
              >
                View my portfolio
              </Link>
            </div>
          </div>
        </section>

        {/* Soft divider */}
        <div className={styles.divider} />

        {/* TECH STACK */}
        <section className={styles.section}>
          <div className={styles.techStack}>
            <p className={styles.techHeading}>
              <strong>Tech stack:</strong>
            </p>

            <ul className={styles.techList}>
              <li>Docs-as-Code tools</li>
              <li>Markdown-based authoring</li>
              <li>Version control workflows (Git)</li>
              <li>API documentation (REST, OpenAPI/Swagger)</li>
              <li>Developer tooling &amp; API testing</li>
              <li>Visual design tools</li>
              <li>SEO and content optimization frameworks</li>
              <li>AI-assisted doc workflows</li>
            </ul>
          </div>
        </section>

      </main>
    </Layout>
  );
}