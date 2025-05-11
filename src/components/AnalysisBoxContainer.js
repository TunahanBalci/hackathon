import { useAnalysis } from "../provider/AnalysisContext";
import styles from "./AnalysisBoxContainer.module.css";
import React from "react";
function AnalysisBoxContainer() {
  const { analiz, yag_orani, bmi, bko } = useAnalysis();
  return (
    <div className={styles["analysis-box-container"]}>
      <div className={styles["analysis-box"]}>
        <h3>Analiz Bilgisi</h3>
        <p>Vücut yağ oranı: {yag_orani}</p>
        <p>BMI (Vücut Kitle İndeksi): {bmi}</p>
        <p>BKO (Bel Kalça Oranı): {bko}</p>
      </div>
      <div className={styles["overall-analysis-box"]}>
        <h3>Sizi nasıl gözlemledik?</h3>
        <p>{analiz}</p>
      </div>
    </div>
  );
}

export default AnalysisBoxContainer;
