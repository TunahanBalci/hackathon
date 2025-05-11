import React, { useState, useRef, useEffect } from "react";
import LoadingScreen from "./LoadingScreen";
import styles from "./FormPanel.module.css";
import Results from "./Results";

const FormPanel = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [images, setImages] = useState([]);
  const [gender, setGender] = useState("");
  const [formHeight, setFormHeight] = useState(0);
  const [isResultsOpen, setIsResultsOpen] = useState(false);

  const formRef = useRef(null);

  // Measure form height on mount & resize
  useEffect(() => {
    const updateHeight = () => {
      if (formRef.current) {
        setFormHeight(formRef.current.clientHeight);
      }
    };
    updateHeight();
    window.addEventListener("resize", updateHeight);
    return () => window.removeEventListener("resize", updateHeight);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setIsResultsOpen(true);
    }, 1500);
  };

  const handleCloseResults = () => {
    setIsResultsOpen(false);
  };

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    const newImgs = files.map((f) => ({
      file: f,
      url: URL.createObjectURL(f),
    }));
    setImages((prev) => [...prev, ...newImgs]);
  };

  const handleGenderChange = (e) => setGender(e.target.value);

  const showOverlay = images.length > 3;
  const previews = images.slice(0, 3);

  if (isLoading) return <LoadingScreen />;

  return isResultsOpen ? (
    <Results handleCloseResults={handleCloseResults}></Results>
  ) : (
    <section className={styles.container}>
      <div className={styles.card}>
        <form ref={formRef} className={styles.form} onSubmit={handleSubmit}>
          <h2 className={styles.heading}>Kullanıcı Bilgileri</h2>

          <label htmlFor="fullName">Ad Soyad</label>
          <input id="fullName" type="text" placeholder="Ad Soyad" />

          <label htmlFor="age">Yaş</label>
          <input id="age" type="number" placeholder="Yaş" />

          <label htmlFor="height">Boy (cm)</label>
          <input id="height" type="number" placeholder="Boy" />

          <label htmlFor="weight">Kilo (kg)</label>
          <input id="weight" type="number" placeholder="Kilo" />

          <label htmlFor="waist">Bel Genişliği (cm)</label>
          <input id="waist" type="number" placeholder="Bel" />

          <label htmlFor="hip">Kalça Genişliği (cm)</label>
          <input id="hip" type="number" placeholder="Kalça" />

          <label>Cinsiyet</label>
          <div className={styles.genderGroup}>
            <label>
              <input
                type="radio"
                name="gender"
                value="Erkek"
                checked={gender === "Erkek"}
                onChange={handleGenderChange}
              />{" "}
              Erkek
            </label>
            <label>
              <input
                type="radio"
                name="gender"
                value="Kadın"
                checked={gender === "Kadın"}
                onChange={handleGenderChange}
              />{" "}
              Kadın
            </label>
          </div>

          <label>Fotoğraf</label>
          <div className={styles.uploadRow}>
            <label htmlFor="imageUpload" className={styles.uploadBox}>
              <div className={styles.uploadContent}>
                <span className={styles.clipIcon}>📎</span>
                <p>Görsel Ekle</p>
                <p className={styles.uploadHint}>(jpg, png)</p>
              </div>
            </label>
            <input
              id="imageUpload"
              type="file"
              accept="image/*"
              multiple
              className={styles.hiddenInput}
              onChange={handleImageUpload}
            />

            {images.length > 0 && (
              <div className={styles.previewBox}>
                {previews.map((img, i) => (
                  <img
                    key={i}
                    src={img.url}
                    alt={`preview-${i}`}
                    className={styles.previewImage}
                  />
                ))}
                {showOverlay && (
                  <div className={styles.previewOverlay}>
                    +{images.length - 3}
                  </div>
                )}
              </div>
            )}
          </div>

          <button type="submit" className={styles.submitButton}>
            Gönder
          </button>
        </form>

        <div className={styles.visualBox} style={{ height: formHeight }}>
          <img src="/imgs/form.png" alt="avatar" />
          <div className={styles.blurBox}></div>
          <div className={styles.visualContent}>
            <h2>Diyet Planı</h2>
            <p>Sağlıklı bir yaşam için ilk adım!</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FormPanel;
