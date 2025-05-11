import React from "react";
import styles from "./ResultIntro.module.css"; // Assuming you have a CSS file for styling
import ProfileCard from "./ProfileCard";
import AnalysisBoxContainer from "./AnalysisBoxContainer";

function ResultIntro() {
  return (
    <div className={styles["result-info-container"]}>
      <ProfileCard />
      <AnalysisBoxContainer></AnalysisBoxContainer>
    </div>
  );
}

export default ResultIntro;
