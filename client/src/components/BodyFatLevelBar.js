import React from "react";
import styles from "./BodyFatLevelBar.module.css";

const BodyFatLevelBar = ({
  bodyFatPercent = 0,
  thresholds = { underfat: 8, healthy: 20, overfat: 25 },
}) => {
  const pct = Math.max(0, Math.min(100, bodyFatPercent));
  const { underfat, healthy, overfat } = thresholds;

  // Find current segment
  let currentKey, currentLabel;
  if (pct < underfat) {
    currentKey = "underfat";
    currentLabel = "Az Yağlı (<8%)";
  } else if (pct < healthy) {
    currentKey = "healthy";
    currentLabel = "Sağlıklı (8–20%)";
  } else if (pct < overfat) {
    currentKey = "overfat";
    currentLabel = "Fazla Yağ (20–25%)";
  } else {
    currentKey = "obese";
    currentLabel = "Obez (≥25%)";
  }

  const segments = [
    { key: "underfat", width: underfat, label: "Az Yağlı (<8%)" },
    { key: "healthy", width: healthy - underfat, label: "Sağlıklı (8–20%)" },
    { key: "overfat", width: overfat - healthy, label: "Fazla Yağ (20–25%)" },
    { key: "obese", width: 100 - overfat, label: "Obez (≥25%)" },
  ];

  return (
    <div className={styles.container}>
      <h4>Vücut Yağ Oranı Grafiği</h4>
      <div className={styles.bar}>
        {segments.map((seg) => (
          <div
            key={seg.key}
            className={`${styles.segment} ${styles[seg.key]}`}
            style={{ flexBasis: `${seg.width}%` }}
          />
        ))}

        {/* marker */}
        <div className={styles.marker} style={{ left: `${pct}%` }}>
          <div className={styles.bubble}>
            <strong style={{ color: `var(--${currentKey}-color)` }}>
              {pct.toFixed(1)}%
            </strong>{" "}
            — {currentLabel}
          </div>
          <div
            className={styles.arrow}
            style={{ color: `var(--${currentKey}-color)` }}
          >
            ▼
          </div>
        </div>
      </div>

      {/* legend */}
      <div className={styles.legend}>
        {segments.map((seg) => (
          <div key={seg.key} className={styles.legendItem}>
            <span
              className={styles.legendColor}
              style={{ background: `var(--${seg.key}-color)` }}
            />
            <span className={styles.legendText}>{seg.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BodyFatLevelBar;
