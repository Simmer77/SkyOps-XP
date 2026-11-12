# ✈️ SkyOps XP12 — Operations & Real Economy Platform

[![X-Plane 12](https://img.shields.io/badge/X--Plane_12-Native_UDP-blue.svg)](https://www.x-plane.com/)
[![Zero Plugins](https://img.shields.io/badge/Plugins_Required-ZERO-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v1.0.0-orange.svg)]()

> **Zero simulator plugins required.** SkyOps XP connects directly to X-Plane 12 via native binary UDP (port 49000).  
> **Nessun plugin richiesto nel simulatore.** SkyOps XP comunica direttamente con X-Plane 12 via socket UDP nativo (porta 49000).

---

## 📖 Documentation / Documentazione
* 🇬🇧 **[English Operations Manual & User Guide (MANUAL_EN.md)](MANUAL_EN.md)**
* 🇮🇹 **[Manuale Operativo e Guida Utente in Italiano (MANUAL_IT.md)](MANUAL_IT.md)**
* 💬 **[Release Notes & Forum Announcement (FORUM_POST.md)](FORUM_POST.md)**

---

## 🌟 Highlights / Caratteristiche Principali

* **✈️ Persistent Fleet & Hangar / Flotta Persistente:**  
  Tracks last parked ICAO airport, residual fuel in tanks, airframe/engine hours, and ownership status (owned, dry leased, or financed).
* **💰 Calibrated Airline Economics (Trip P&L) / Contabilità Realistica:**  
  Full trip profit & loss analysis: commercial yields (passengers, ancillaries, cargo), touchdown quality bonuses (Butter, Good, Hard), landing fees (discounted at home base), ground handling, power-by-the-hour maintenance reserves, and indirect operating costs (IOC).
* **🌍 Global Multi-Region ANSP Navigation Fees / Tariffe di Sorvolo Mondiali:**  
  - **USA Domestic (FAA `K*`/`PA*`/`PH*`):** **$0.00 / €0.00 (FAA Exempt)**.
  - **Europe (Eurocontrol):** Full en-route fee (€65/unit rate) + Terminal radar charge (TNC).
  - **Canada (NAV CANADA):** €55/unit rate.
  - **Australia & New Zealand (Airservices / Airways NZ):** €52/unit rate.
  - **Rest of World (ICAO Regional ANSP):** €40/unit rate.
  - **Universal Exemptions:** All **VFR flights** and aircraft with **MTOW < 2.0 t** (e.g. Cessna 172) pay **$0.00** worldwide.
* **📅 Calendar Operating Month / Mese Operativo:**  
  Fixed hangar and insurance costs follow the real calendar month, ensuring that fixed costs are collected realistically regardless of flight count or multi-month breaks.
* **👨‍✈️ Salaried Staff vs Freelance Crew / Equipaggi Fissi:**  
  Hire dedicated crew on a fixed monthly retainer for $0/h flight fees, or pay hourly freelance rates.
* **🛠️ Workshop & In-Flight Failures / Officina & Avarie Dinamiche:**  
  Simulates wear on engines (EGT/TBO), brakes, tires, and airframe. Neglected maintenance triggers authentic X-Plane 12 dataref failures.
* **🗺️ IVAO & Custom Tours Tracker / Diario & Mappa Tour:**  
  Group flights into custom or network tours with cumulative statistics and interactive route mapping.
* **📱 LAN & Tablet Touch Ready / Accesso da Tablet o Secondo Monitor:**  
  Responsive glass-cockpit dashboard accessible on iPad, Android tablet, or second PC via local Wi-Fi.
* **🌐 Bilingual & Multi-Currency / Bilingue & Multi-Valuta:**  
  Full English & Italian localization with instant toggle between **EUR (€)** and **USD ($)**.

---

## 🚀 Quick Start / Avvio Rapido

### Windows
1. Download and unzip the release package.
2. Ensure [Python 3.10+](https://www.python.org/downloads/) is installed with *"Add python.exe to PATH"* checked.
3. Double-click **`run.bat`**.
4. Open your browser at:
   ```text
   http://localhost:8000
   ```

### Linux & macOS
1. Open a terminal in the extracted folder.
2. Run:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
3. Open your browser at `http://localhost:8000`.

---

## 📄 License
Released under the [MIT License](LICENSE).
