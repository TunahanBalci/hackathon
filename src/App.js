import React from "react";
import styles from "./App.module.css";
import FormPanel from "./components/FormPanel";

function App() {
  return (
    <main className={styles["main-layout"]}>
      <FormPanel />
    </main>
  );
}

export default App;
