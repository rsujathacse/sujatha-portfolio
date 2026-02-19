import React from "react";
import Layout from "@theme/Layout";
import PortfolioSidebar from "../../components/PortfolioSidebar"; // ✅ IMPORTANT path

export default function WritingTheFuture() {
  return (
    <Layout title="Writing the Future">
      <div
        style={{
          display: "flex",
          gap: "24px",
          alignItems: "flex-start",
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "24px 16px",
        }}
      >
        

        {/* ✅ MAIN CONTENT */}
        <main style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              background: "white",
              borderRadius: "16px",
              padding: "32px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
              maxWidth: "900px",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Writing the Future</h2>

            <p style={{ fontWeight: 500 }}>
              TECH WRITE PRO – ITCI 2nd Bengaluru Conference
              <br />
              April 12–13, 2024
            </p>

            {/* Image */}
            <div style={{ margin: "24px 0" }}>
              <img
                src="/img/talks/writing-the-future.png"
                alt="Writing the Future cover slide"
                style={{
                  width: "100%",
                  borderRadius: "12px",
                  boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
                }}
              />
            </div>

            <p>
              In my “Writing the Future” session, I explored how technical
              writers must evolve in an AI world—combining storytelling, visual
              literacy, emotional intelligence, and SEO strategy.
            </p>

            <p>
              The session covered the evolution of technical writing, emerging
              roles like AR/VR writers and software interpreters, and practical
              frameworks for clean writing.
            </p>

            <div style={{ marginTop: "24px" }}>
              <a
                className="button button--primary"
                href="/files/Writing-the-Future-Sujatha-R.pdf"
                target="_blank"
                rel="noopener noreferrer"
              >
                View Presentation →
              </a>
            </div>
          </div>
        </main>
      </div>
    </Layout>
  );
}