// src/context/AnalysisContext.js
import React, { createContext, useContext, useState } from "react";

const AnalysisContext = createContext(null);

export const AnalysisProvider = ({ children }) => {
  const [analysisState, setAnalysisState] = useState();

  const updateAnalysis = (newData) => {
    setAnalysisState((prevState) => ({
      ...prevState,
      ...newData,
    }));
  };

  return (
    <AnalysisContext.Provider value={{ ...analysisState, updateAnalysis }}>
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
