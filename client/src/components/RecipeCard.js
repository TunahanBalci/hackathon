import React from "react";
import styles from "./RecipeCard.module.css";

const RecipeCard = ({ image, title, description, ingredients }) => (
  <div className={styles["recipe-card"]}>
    <img src={image} alt={title} />
    <div className={styles["card-content"]}>
      <h3>{title}</h3>
      <p>{description}</p>
      <ul>
        {ingredients.map((item, index) => <li key={index}>{item}</li>)}
      </ul>
    </div>
  </div>
);

export default RecipeCard;