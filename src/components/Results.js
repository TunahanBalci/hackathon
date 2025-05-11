import React from "react";
import styles from "./Results.module.css";
import RecipeCard from "./RecipeCard";
import RecipeDetail from "./RecipeDetail";
import BodyFatLevelBar from "./BodyFatLevelBar.js";
import AnalysisBoxContainer from "./AnalysisBoxContainer.js";
import WeeklyPlan from "./WeeklyPlan.jsx";
import { useAnalysis } from "../provider/AnalysisContext.js";
import ProfileCard from "./ProfileCard.js";
import ResultIntro from "./ResultIntro.js";
import BmiLevelBar from "./BmiLevelBar.js";
import BkoLevelBar from "./BkoLevelBar.js";

const Results = ({ handleCloseResults }) => {
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
  } = useAnalysis();

  return (
    <section className={styles["results-panel"]}>
      <div className={styles["card"]}>
        <p className={styles["close-p"]} onClick={handleCloseResults}>
          Yeniden Form Gönder
        </p>
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
