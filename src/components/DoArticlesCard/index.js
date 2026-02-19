import React, { useMemo, useState } from "react";
import articles from "../../data/doArticles.json";

const CATEGORIES = [
  "Foundations",
  "Listicles",
  "Versus (vs) articles",
  "Misc",
];

function normalizeCategory(cat) {
  const c = (cat || "").trim();
  return CATEGORIES.includes(c) ? c : "Misc";
}

export default function DoArticlesCard() {
  // Normalize categories so anything unknown becomes Misc
  const normalized = useMemo(() => {
    return (articles || []).map((a) => ({
      ...a,
      category: normalizeCategory(a.category),
      title: (a.title || "").trim(),
      description: (a.description || "").trim(),
      url: (a.url || "").trim(),
    }));
  }, []);

  const [selected, setSelected] = useState("Foundations");

  const filtered = useMemo(() => {
    return normalized
      .filter((a) => a.category === selected && a.title && a.url)
      .sort((a, b) => a.title.localeCompare(b.title));
  }, [normalized, selected]);

  return (
    <div
      style={{
        border: "1px solid #e3e3e3",
        borderRadius: "12px",
        padding: "20px",
        width: "520px",
        maxWidth: "100%",
        boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
        background: "var(--ifm-background-surface-color)",
      }}
    >
      <h3 style={{ marginTop: 0 }}>
        Select articles that I wrote for DigitalOcean
      </h3>

      <div style={{ marginTop: "10px", marginBottom: "14px" }}>
        <div style={{ fontWeight: 700, marginBottom: "8px" }}>
          Choose your category:
        </div>

        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          style={{
            width: "100%",
            padding: "10px 12px",
            borderRadius: "10px",
            border: "1px solid #d7d7d7",
            background: "transparent",
            fontSize: "15px",
          }}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Two-column Title | Description */}
      {filtered.length > 0 ? (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th
                  style={{
                    textAlign: "left",
                    padding: "10px 8px",
                    borderBottom: "1px solid rgba(0,0,0,0.12)",
                    width: "42%",
                  }}
                >
                  Title
                </th>
                <th
                  style={{
                    textAlign: "left",
                    padding: "10px 8px",
                    borderBottom: "1px solid rgba(0,0,0,0.12)",
                  }}
                >
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.url}>
                  <td
                    style={{
                      verticalAlign: "top",
                      padding: "10px 8px",
                      borderBottom: "1px solid rgba(0,0,0,0.06)",
                      fontWeight: 600,
                    }}
                  >
                    <a href={a.url} target="_blank" rel="noreferrer">
                      {a.title}
                    </a>
                  </td>
                  <td
                    style={{
                      verticalAlign: "top",
                      padding: "10px 8px",
                      borderBottom: "1px solid rgba(0,0,0,0.06)",
                      lineHeight: "1.55",
                    }}
                  >
                    {a.description || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p style={{ margin: 0 }}>
          No articles found in <b>{selected}</b>. Add entries to{" "}
          <code>src/data/doArticles.json</code>.
        </p>
      )}
    </div>
  );
}