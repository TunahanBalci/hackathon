import React, { useState, useRef, useEffect } from "react";
import LoadingScreen from "./LoadingScreen";
import styles from "./FormPanel.module.css";
import Results from "./Results";
import { useAnalysis } from "../provider/AnalysisContext";

const FormPanel = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [images, setImages] = useState();
  const [gender, setGender] = useState("");
  const [formHeight, setFormHeight] = useState(0);
  const [isResultsOpen, setIsResultsOpen] = useState(false);
  const { updateAnalysis } = useAnalysis();

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Get form data
      const formData = new FormData();
      const fullName = document.getElementById("fullName").value;
      const age = document.getElementById("age").value;
      const height = document.getElementById("height").value;
      const weight = document.getElementById("weight").value;
      const waist = document.getElementById("waist").value;
      const hip = document.getElementById("hip").value;

      // Create user profile
      const userProfile = {
        fullName,
        age: parseInt(age),
        gender: gender,
        measurements: {
          height_cm: parseInt(height),
          weight_kg: parseFloat(weight),
          waist_cm: parseInt(waist),
          hip_cm: parseInt(hip),
        },
      };

      console.log("User Profile:", userProfile);

      // Create a user ID (you might want to use a proper authentication system)
      const userId = "user_" + Date.now();

      // First, create/update user profile
      const profileResponse = await fetch(
        `http://localhost:5000/profile/${userId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(userProfile),
          credentials: "include",
          mode: "cors",
        }
      );

      if (!profileResponse.ok) {
        const errorData = await profileResponse.json();
        throw new Error(
          `Failed to create user profile: ${
            errorData.error || profileResponse.statusText
          }`
        );
      }

      // If there are images, analyze them
      if (images != null) {
        const imageFormData = new FormData();
        imageFormData.append("photo", images.file);

        const analysisResponse = await fetch(
          `http://localhost:5000/analyze-photo/${userId}`,
          {
            method: "POST",
            body: imageFormData,
            credentials: "include",
            mode: "cors",
          }
        );

        if (!analysisResponse.ok) {
          const errorData = await analysisResponse.json();
          throw new Error(
            `Failed to analyze photo: ${
              errorData.error || analysisResponse.statusText
            }`
          );
        }

        const analysisData = await analysisResponse.json();

        // Update the AnalysisContext with the response data
        console.log("Analysis data:", analysisData);
        updateAnalysis(analysisData);
        setIsLoading(false);
        setIsResultsOpen(true);
      } else {
        // If no images, just show the profile
        updateAnalysis(userProfile);
        setIsLoading(false);
        setIsResultsOpen(true);
      }
    } catch (error) {
      console.error("Detailed error:", error);
      setIsLoading(false);
      alert(`An error occurred: ${error.message}`);
    }

    setImages([]);
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
    setImages(newImgs[0]);
  };

  const handleGenderChange = (e) => setGender(e.target.value);

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

            {images?.url && (
              <div className={styles.previewBox}>
                <img
                  key={images.url}
                  src={images.url}
                  alt="preview"
                  className={styles.previewImage}
                />
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
