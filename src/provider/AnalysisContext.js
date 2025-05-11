// src/context/AnalysisContext.js
import React, { createContext, useContext } from "react";
import analysisData from "../components/analiz_sonucu.json";

const AnalysisContext = createContext(null);

export const AnalysisProvider = ({ children }) => {
  return (
    <AnalysisContext.Provider value={analysisData}>
      {children}
    </AnalysisContext.Provider>
  );
};

/** Hook to consume the analysis data */
export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (context === null) {
    throw new Error("useAnalysis must be used within an AnalysisProvider");
  }
  return context;
};
