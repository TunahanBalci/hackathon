import React, { useState } from "react";
import styles from "./SubscriptionPopup.module.css";

const packages = [
  {
    name: "Basic",
    price: "₺49 / ay",
    features: ["Özellik A", "Özellik B", "Destek"],
  },
  {
    name: "Pro",
    price: "₺99 / ay",
    features: ["Tüm Basic özellikler", "Ekstra C", "Öncelikli Destek"],
  },
  {
    name: "Premium",
    price: "₺199 / ay",
    features: ["Tüm Pro özellikler", "Özel D", "Kişisel Danışman"],
  },
];

export default function SubscriptionPopup() {
  const [isOpen, setIsOpen] = useState(false);

  // Open modal
  const handleOpen = () => setIsOpen(true);
  // Close modal
  const handleClose = () => setIsOpen(false);

  return (
    <>
      {/* Fixed subscription button */}
      <button
        className={styles.fab}
        onClick={handleOpen}
        aria-label="Open subscription options"
      >
        💳 Abone Ol
      </button>

      {/* Modal overlay */}
      {isOpen && (
        <div className={styles.overlay} onClick={handleClose}>
          {/* Modal content */}
          <div
            className={styles.modal}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="subscription-title"
          >
            <h2 id="subscription-title">Paket Seçenekleri</h2>

            <div className={styles.packages}>
              {packages.map((pkg) => (
                <div key={pkg.name} className={styles.card}>
                  <h3>{pkg.name}</h3>
                  <p className={styles.price}>{pkg.price}</p>
                  <ul>
                    {pkg.features.map((f) => (
                      <li key={f}>✔️ {f}</li>
                    ))}
                  </ul>
                  <button
                    className={styles.selectButton}
                    onClick={() =>
                      alert(`"${pkg.name}" paketine yönlendiriliyorsunuz.`)
                    }
                  >
                    {pkg.name}’a Geç
                  </button>
                </div>
              ))}
            </div>

            <button
              className={styles.close}
              onClick={handleClose}
              aria-label="Close"
            >
              ✖️
            </button>
          </div>
        </div>
      )}
    </>
  );
}
