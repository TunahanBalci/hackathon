import React from "react";
import styles from "./WeeklyPlan.module.css";

// Define the Turkish week order:
const WEEK_DAYS = [
  "Pazartesi",
  "Salı",
  "Çarşamba",
  "Perşembe",
  "Cuma",
  "Cumartesi",
  "Pazar",
];

const WeeklyPlan = ({ diyet_listesi, egzersiz_programi }) => {
  // Build a lookup by day for fast access:
  const exerciseByDay = egzersiz_programi.reduce((acc, item) => {
    acc[item.gun] = item.egzersiz;
    return acc;
  }, {});
  const dietByDay = diyet_listesi.reduce((acc, item) => {
    acc[item.gun] = item;
    return acc;
  }, {});

  return (
    <div className={styles.weeklyContainer}>
      {WEEK_DAYS.map((day) => (
        <div key={day} className={styles.dayCard}>
          <h3 className={styles.dayTitle}>{day}</h3>

          <div className={styles.sections}>
            {/* Exercise Section */}
            <div className={styles.section}>
              <h4>Egzersiz</h4>
              <div
                className={styles.exerciseText}
                dangerouslySetInnerHTML={{
                  __html: exerciseByDay[day]
                    ?.replace(/\n/g, "<br/>")
                    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"),
                }}
              />
            </div>

            {/* Diet Section */}
            <div className={`${styles.section} ${styles.animatedSection}`}>
              <h4>Diyet</h4>
              {dietByDay[day] ? (
                <table className={styles.dietTable}>
                  <tbody>
                    <tr>
                      <th>Kahvaltı</th>
                      <td>{dietByDay[day].kahvalti}</td>
                    </tr>
                    <tr>
                      <th>Öğle</th>
                      <td>{dietByDay[day].ogle}</td>
                    </tr>
                    <tr>
                      <th>Akşam</th>
                      <td>{dietByDay[day].aksam}</td>
                    </tr>
                    <tr>
                      <th>Ara Öğün</th>
                      <td>{dietByDay[day].ara_ogun}</td>
                    </tr>
                    <tr className={styles.caloriesRow}>
                      <th>Kalori</th>
                      <td>{dietByDay[day].toplam_kalori} kcal</td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <p>Veri yok</p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default WeeklyPlan;
