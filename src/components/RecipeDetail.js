import React from "react";
import styles from "./RecipeDetail.module.css";

const RecipeDetail = () => (
  <div className={styles["recipe-detail"]}>
    <h3>Tarif Detayı</h3>
    <img
      src="https://i.nefisyemektarifleri.com/2021/04/07/firinda-somonbaligi.jpg"
      alt="Fırında Somon"
    />
    <p>
      <strong>Tarif adı:</strong> Fırında Somon ve Kinoalı Sebze Yatağı
    </p>
    <p>
      <strong>Malzemeler:</strong> Somon fileto, haşlanmış kinoa, brokoli, havuç,
      kabak, sarımsak, limon suyu, kekik, tuz, zeytinyağı
    </p>
    <p>
      <strong>Hazırlık:</strong> Sebzeleri ve kinoayı haşlayın. Marine edilmiş somonla
      birlikte fırın kabına yerleştirin. 180°C'de 25 dakika pişirin.
    </p>
  </div>
);

export default RecipeDetail;