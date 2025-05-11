import React, { useRef } from "react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

import styles from "./Results.module.css";
import BodyFatLevelBar from "./BodyFatLevelBar";
import AnalysisBoxContainer from "./AnalysisBoxContainer";
import WeeklyPlan from "./WeeklyPlan";
import { useAnalysis } from "../provider/AnalysisContext";
import ProfileCard from "./ProfileCard";
import ResultIntro from "./ResultIntro";
import BmiLevelBar from "./BmiLevelBar";
import BkoLevelBar from "./BkoLevelBar";

const Results = ({ handleCloseResults }) => {
  const panelRef = useRef(null);
  const {
    boy,
    kilo,
    analiz,
    yag_orani,
    yas,
    cinsiyet,
    bel,
    kalca,
    bmi,
    bmi_yorum,
    bko,
    bko_yorum,
    egzersiz_programi,
    diyet_listesi,
    fullName,
    avatarUrl,
  } = useAnalysis();

  const handleDownloadPdf = async () => {
    if (!panelRef.current) return;
    const canvas = await html2canvas(panelRef.current, { scale: 2 });
    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF({ unit: "pt", format: "a4" });
    const width = pdf.internal.pageSize.getWidth();
    const height = (canvas.height * width) / canvas.width;
    pdf.addImage(imgData, "PNG", 0, 0, width, height);
    pdf.save("diyet-sonuclari.pdf");
  };

  return (
    <section className={styles["results-panel"]} ref={panelRef}>
      <div className={styles["card"]}>
        <div className={styles["actions"]}>
          <button
            onClick={() => window.print()}
            className={styles["pdf-button"]}
          >
            📄 PDF Olarak Kaydet
          </button>
          <span onClick={handleCloseResults} className={styles["close-p"]}>
            🔄 Yeniden Form Gönder
          </span>
        </div>

        <h2>Sonuçlar & Diyet Programınız</h2>
        <ResultIntro />

        <BodyFatLevelBar bodyFatPercent={yag_orani} />

        <BmiLevelBar bmi={bmi} />

        <BkoLevelBar ratio={bko} />

        <WeeklyPlan
          diyet_listesi={diyet_listesi}
          egzersiz_programi={egzersiz_programi}
        />
      </div>
    </section>
  );
};

export default Results;
