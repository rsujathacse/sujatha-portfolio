import React from "react";
import styles from "./styles.module.css";

export default function ArticleCard({ title, description, imgSrc, href }) {
  return (
    <article className={styles.card}>
      <div className={styles.media}>
        {/* eslint-disable-next-line @docusaurus/no-html-link */}
        <a href={href} target="_blank" rel="noopener noreferrer" aria-label={title}>
          <img className={styles.image} src={imgSrc} alt={title} loading="lazy" />
        </a>
      </div>

      <div className={styles.body}>
        <h3 className={styles.title}>{title}</h3>
        {description ? <p className={styles.desc}>{description}</p> : null}

        {/* eslint-disable-next-line @docusaurus/no-html-link */}
        <a className={styles.cta} href={href} target="_blank" rel="noopener noreferrer">
          Read this article →
        </a>
      </div>
    </article>
  );
}