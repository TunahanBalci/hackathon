import React from "react";
import styles from "./ProfileCard.module.css";
import { useAnalysis } from "../provider/AnalysisContext";

const ProfileCard = () => {
  const { cinsiyet, yas, boy, kilo, bel, kalca } = useAnalysis();

  return (
    <div className={styles.card}>
      <div className={styles.info}>
        <p>
          ⚧ Cinsiyet: <strong>{cinsiyet}</strong>
        </p>
        <p>
          🎂 Yaş: <strong>{yas} yaş</strong>
        </p>
        <p>
          📏 Boy: <strong>{boy} cm</strong>
        </p>
        <p>
          ⚖️ Kilo: <strong>{kilo} kg</strong>
        </p>
        <p>
          🔄 Bel: <strong>{bel} cm</strong>
        </p>
        <p>
          🔄 Kalça: <strong>{kalca} cm</strong>
        </p>
      </div>
    </div>
  );
};

export default ProfileCard;
