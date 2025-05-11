import React from "react";
import styles from "./ProfileCard.module.css";
import { useAnalysis } from "../provider/AnalysisContext";

const ProfileCard = () => {
  const { imageUrl, adSoyad, cinsiyet, yas, boy, kilo, bel, kalça } =
    useAnalysis();

  return (
    <div className={styles.card}>
      <img src={imageUrl} alt={`${adSoyad}`} className={styles.avatar} />

      <div className={styles.info}>
        <h3 className={styles.name}>👤 {adSoyad}</h3>
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
          🔄 Kalça: <strong>{kalça} cm</strong>
        </p>
      </div>
    </div>
  );
};

export default ProfileCard;
