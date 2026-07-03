import React from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";

export default function Talks() {
  return (
    <Layout
      title="My talks"
      description="Talks, presentations, cloud, and AI/ML learning videos by Sujatha R."
    >
      <main
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "32px 16px",
        }}
      >
        <h1 style={{ marginBottom: "8px" }}>My talks</h1>

        <p style={{ fontSize: "18px", marginBottom: "32px" }}>
          A collection of my talks, presentations, and AI/ML explainers.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
            gap: "24px",
          }}
        >
          {/* Writing the Future card */}
          <div
            style={{
              background: "white",
              borderRadius: "16px",
              padding: "24px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
            }}
          >
            <img
              src="/img/talks/writing-the-future.png"
              alt="Writing the Future cover slide"
              style={{
                width: "100%",
                borderRadius: "12px",
                boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
                marginBottom: "20px",
              }}
            />

            <h2 style={{ marginTop: 0 }}>Writing the Future</h2>

            <p style={{ fontWeight: 500 }}>
              TECH WRITE PRO, ITCI 2nd Bengaluru Conference
              <br />
              April 12 to 13, 2024
            </p>

            <p>
              In this session, I explored how technical writers must evolve in
              an AI world by combining storytelling, visual literacy, emotional
              intelligence, and SEO strategy.
            </p>

            <Link
              className="button button--primary"
              to="/talks/writing-the-future"
            >
              View talk →
            </Link>
          </div>

          {/* RAG YouTube video card */}
          <div
            style={{
              background: "white",
              borderRadius: "16px",
              padding: "24px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
            }}
          >
            <a
              href="https://youtu.be/ZdrF0z5P5MQ"
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                src="/img/talks/Sujatha R RAG YT thumbnail.png"
                alt="Learn RAG Basics in less than 5 minutes YouTube thumbnail"
                style={{
                  width: "100%",
                  borderRadius: "12px",
                  boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
                  marginBottom: "20px",
                }}
              />
            </a>

            <h2 style={{ marginTop: 0 }}>Learn RAG Basics in &lt; 5 mins</h2>

            <p style={{ fontWeight: 500 }}>
              AI/ML Conceptual video
              <br />
        
            </p>

            <p>
              RAG is one of the most important concepts behind modern AI apps,
              chatbots, knowledge assistants, and AI agents. In this video, I
              explain what RAG is, how it works, why it reduces hallucinations,
              and where it is used in real-world AI systems.
            </p>

            <details style={{ marginTop: "16px", marginBottom: "24px" }}>
              <summary style={{ cursor: "pointer", fontWeight: 600 }}>
                View chapters
              </summary>

              <ul style={{ marginTop: "12px" }}>
                <li>
                  <a
                    href="https://www.youtube.com/watch?v=ZdrF0z5P5MQ"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    0:00, Can AI stay accurate?
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.youtube.com/watch?v=ZdrF0z5P5MQ&t=14s"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    0:14, Overview
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.youtube.com/watch?v=ZdrF0z5P5MQ&t=20s"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    0:20, What is RAG?
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.youtube.com/watch?v=ZdrF0z5P5MQ&t=60s"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    1:00, How RAG works
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.youtube.com/watch?v=ZdrF0z5P5MQ&t=153s"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    2:33, Challenges of building RAG
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.youtube.com/watch?v=ZdrF0z5P5MQ&t=214s"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    3:34, RAG use cases
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.youtube.com/watch?v=ZdrF0z5P5MQ&t=242s"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    4:02, RAG recap for interviews
                  </a>
                </li>
              </ul>
            </details>

            <a
              className="button button--primary"
              href="https://youtu.be/ZdrF0z5P5MQ"
              target="_blank"
              rel="noopener noreferrer"
            >
              Watch on YouTube →
            </a>
          </div>
        </div>
      </main>
    </Layout>
  );
}
