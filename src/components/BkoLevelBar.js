import React from "react";
import styles from "./BkoLevelBar.module.css";

const BkoLevelBar = ({
  ratio = 0,
  thresholds = { low: 0.9, moderate: 1.0 },
}) => {
  const pct = Math.max(0, Math.min(1.2, ratio));
  let currentKey, currentLabel;

  if (pct < thresholds.low) {
    currentKey = "low";
    currentLabel = "Düşük Risk (<0.9)";
  } else if (pct < thresholds.moderate) {
    currentKey = "moderate";
    currentLabel = "Orta Risk (0.9–1.0)";
  } else {
    currentKey = "high";
    currentLabel = "Yüksek Risk (>1.0)";
  }

  const segments = [
    {
      key: "low",
      width: (thresholds.low / 1.2) * 100,
      label: "Düşük Risk (<0.9)",
    },
    {
      key: "moderate",
      width: ((thresholds.moderate - thresholds.low) / 1.2) * 100,
      label: "Orta Risk (0.9–1.0)",
    },
    {
      key: "high",
      width: ((1.2 - thresholds.moderate) / 1.2) * 100,
      label: "Yüksek Risk (>1.0)",
    },
  ];

  return (
    <div className={styles.container}>
      <h4>Vücut BKO (Bel Kalça Oranı) Grafiği</h4>
      <div className={styles.bar}>
        {segments.map((seg) => (
          <div
            key={seg.key}
            className={`${styles.segment} ${styles[seg.key]}`}
            style={{ flexBasis: `${seg.width}%` }}
          />
        ))}
        <div
          className={styles.marker}
          style={{ left: `${(pct / 1.2) * 100}%` }}
        >
          <div className={styles.bubble}>
            <strong style={{ color: `var(--${currentKey}-color)` }}>
              {pct.toFixed(2)}
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

export default BkoLevelBar;
