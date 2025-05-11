import React from "react";
import styles from "./LoadingScreen.module.css";

const LoadingScreen = () => {
  return (
    <div className={styles.container}>
      <div className={styles.emoji}>🥗</div>
      <h1 className={styles.message}>Diyet planınız hazırlanıyor...</h1>
      <p className={styles.subtext}>Sağlıklı bir yaşam için ilk adım 🌿</p>
    </div>
  );
};

export default LoadingScreen;
