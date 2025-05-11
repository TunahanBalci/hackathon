import React from "react";
import styles from "./App.module.css";
import FormPanel from "./components/FormPanel";
import SubscriptionPopup from "./components/SubscriptionPopup"; // Import SubscriptionPopup

function App() {
  return (
    <main className={styles["main-layout"]}>
      <FormPanel />
      <SubscriptionPopup />
    </main>
  );
}

export default App;
