import React from 'react';
import Layout from '@theme/Layout';
import styles from './content-strategy.module.css';

export default function ContentStrategy() {
  return (
    <Layout title="Content Strategy">
      <div className={styles.container}>

        <div className={styles.card}>

          <img
            src="/img/strategy/full-funnel-architecture.png"
            alt="Full Funnel Technical Content Strategy Architecture"
            className={styles.image}
          />

          <h1>Full-Funnel Technical Content Strategy</h1>

          <p>
            A structured, intent-driven framework that aligns technical content
            with developer behavior and measurable business outcomes. This model
            connects awareness, evaluation, and implementation into a cohesive
            system that accelerates adoption, reduces friction, and strengthens
            long-term retention.
          </p>

          <a
            href="/docs/strategy/full-funnel-technical-content-strategy"
            className={styles.button}
          >
            Explore the Full Framework →
          </a>

        </div>

      </div>
    </Layout>
  );
}