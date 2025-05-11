import React from "react";
import styles from "./BmiLevelBar.module.css";

const BmiLevelBar = ({
  bmi = 0,
  thresholds = { underweight: 18.5, normal: 24.9, overweight: 29.9 },
}) => {
  const value = Math.max(0, Math.min(40, bmi)); // cap at 40 for display
  const { underweight, normal, overweight } = thresholds;

  let currentKey, currentLabel;
  if (value < underweight) {
    currentKey = "underweight";
    currentLabel = "Zayıf (<18.5)";
  } else if (value <= normal) {
    currentKey = "normal";
    currentLabel = "Normal (18.5–24.9)";
  } else if (value <= overweight) {
    currentKey = "overweight";
    currentLabel = "Fazla Kilolu (25–29.9)";
  } else {
    currentKey = "obese";
    currentLabel = "Obez (≥30)";
  }

  const segments = [
    {
      key: "underweight",
      width: (underweight / 40) * 100,
      label: "Zayıf (<18.5)",
    },
    {
      key: "normal",
      width: ((normal - underweight) / 40) * 100,
      label: "Normal (18.5–24.9)",
    },
    {
      key: "overweight",
      width: ((overweight - normal) / 40) * 100,
      label: "Fazla Kilolu (25–29.9)",
    },
    {
      key: "obese",
      width: ((40 - overweight) / 40) * 100,
      label: "Obez (≥30)",
    },
  ];

  return (
    <div className={styles.container}>
      <h4>Vücut BMI (Vücut Kitle Endeksi) Grafiği</h4>
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
          style={{ left: `${(value / 40) * 100}%` }}
        >
          <div className={styles.bubble}>
            <strong style={{ color: `var(--${currentKey}-color)` }}>
              {value.toFixed(1)}
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

export default BmiLevelBar;
