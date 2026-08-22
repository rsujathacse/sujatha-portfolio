import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import styles from "./styles.module.css";

export function AimlIntroGrid({ children }) {
  return <div className={styles.grid}>{children}</div>;
}

export default function AimlIntroCard({
  imgSrc,
  imgAlt,
  title,
  description,
  to,
  cta = "Read article →",
}) {
  return (
    <div className={styles.card}>
      <img
        className={styles.image}
        src={useBaseUrl(imgSrc)}
        alt={imgAlt}
      />
      <div className={styles.body}>
        <h2 className={styles.title}>{title}</h2>
        <p className={styles.description}>{description}</p>
        <Link to={to} className={styles.cta}>
          {cta}
        </Link>
      </div>
    </div>
  );
}
