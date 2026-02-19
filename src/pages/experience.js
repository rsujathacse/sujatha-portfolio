import React from "react";
import Layout from "@theme/Layout";
import styles from "./experience.module.css";

const navItems = [
  { to: "/aiml/intro", label: "AI/ML Docs" },
  { to: "/docs/intro", label: "Docs" },
  { to: "/apis/intro", label: "APIs" },
  { to: "/architecture/intro", label: "Architecture" },
  { to: "/strategy/intro", label: "Content Strategy" },
];

function Role({ company, title, location, dates, bullets }) {
  return (
    <section className={styles.roleBlock}>
      <div className={styles.roleHeader}>
        <div>
          <h3 className={styles.roleTitle}>{company}</h3>
          <div className={styles.company}>{title}</div>
          <div className={styles.meta}>{location}</div>
        </div>
        <div className={styles.date}>{dates}</div>
      </div>

      <ul className={styles.bullets}>
        {bullets.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
    </section>
  );
}

function InfoBlock({ title, children }) {
  return (
    <section className={styles.infoBlock}>
      <h2 className={styles.infoTitle}>{title}</h2>
      {children}
    </section>
  );
}

export default function Experience() {
  return (
    <Layout title="Experience" description="Experience and portfolio overview">
      <div className={styles.wrapper}>
        {/* LEFT SIDEBAR */}
        <aside className={styles.sidebar}>
          <div className={styles.sidebarTitle}>PORTFOLIO</div>
          <nav>
            <ul className={styles.navList}>
              {navItems.map((item) => (
                <li key={item.to} className={styles.navItem}>
                  <a className={styles.navLink} href={item.to}>
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        {/* RIGHT CONTENT */}
        <main className={styles.content}>
          <div className={styles.contentInner}>
            <h1 className={styles.pageTitle}>EXPERIENCE</h1>

            <p className={styles.objective}>
              Accomplished Senior Technical Writer with 10+ years of experience creating clear, concise,
              and impactful documentation for technical and non-technical audiences.
            </p>

           

            {/* EXPERIENCE */}
            <Role
              company="DigitalOcean"
              title="Technical Writer"
              location="Remote, India"
              dates="Jan 2024 – Present"
              bullets={[
                "Authored 70+ long-form technical articles; several rank on page 1 for competitive cloud and AI keywords and entering top signup-driven UVEC contributors.",
                "Applied cloud and AI/ML concepts to accurately document complex systems with data pipelines, model workflows, platform integrations.",
                "Worked across cloud and observability fundamentals: metrics, monitoring end-to-end data flows.",
              ]}
            />

            <Role
              company="Freelance"
              title="Senior Technical Writer"
              location="Remote, India"
              dates="Oct 2020 – Apr 2023"
              bullets={[
                "Increased user satisfaction by 30% by crafting and maintaining technical documents for multiple startups.",
                "Implemented accessibility-focused content practices via technical guides and supporting technical videos (scriptwriting + editorial refinement) to improve discoverability and inclusivity.",
              ]}
            />

            <Role
              company="Capgemini Tech Services Ind Ltd"
              title="Senior Technical Writer"
              location="Hyderabad, India"
              dates="Jul 2018 – Sept 2020"
              bullets={[
                "Improved documentation quality by 30% by establishing a documentation review process and providing actionable feedback for clarity, accuracy, and consistency.",
                "Guided and mentored a team of 5 technical writers creating and maintaining comprehensive documentation aligned with product updates and user feedback.",
              ]}
            />

            <Role
              company="Fujitsu Limited"
              title="Technical Writer"
              location="Chennai, India"
              dates="Aug 2017 – Jan 2018"
              bullets={[
                "Engineered a knowledge-sharing platform and curated technical resources for 50+ engineers.",
                "Created an embedded systems glossary with practical, real-world usage examples.",
              ]}
            />

            <Role
              company="L&T Infotech"
              title="Software Engineer"
              location="Chennai, India"
              dates="Nov 2014 – Aug 2017"
              bullets={[
                "Delivered 50+ sets of project documentation across multiple technical languages.",
                "Helped content team by simplify the content creation process and maintained adherence to SOPs and style guidelines.",
              ]}
            />



           {/* NEW: Tech Stack */}
            <InfoBlock title="TECH STACK">
              <p className={styles.infoText}>
                Git, HTML, Markup, Docs-as-Code workflows, structured authoring (DITA), Documentation UX.
              </p>
            </InfoBlock>

            {/* NEW: Education */}
            <InfoBlock title="EDUCATION">
              <p className={styles.infoText}>
                B.Tech. Computer Science and Engineering | SNS College of Technology | Anna University |                 
      9.2 CGPA | May 2014

              </p>
            </InfoBlock>

            {/* NEW: Languages */}
            <InfoBlock title="LANGUAGES">
              <ul className={styles.inlineList}>
                <li>English</li>
                <li>Tamil</li>
                <li>Hindi</li>
                <li>Japanese (JLPT N5 Certified)</li>
              </ul>
            </InfoBlock>
          </div>
        </main>
      </div>
    </Layout>
  );
}