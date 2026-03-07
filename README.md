# AI-Powered Cardiac Rehabilitation Prescriber  

## Overview

The **Cardiac Rehabilitation Prescriber** is a full-stack clinical application designed to dynamically prescribe safe, personalized exercise routines for cardiovascular patients.

Standard fitness applications operate on a "push harder" mentality, which is dangerous in a clinical setting. This application flips that paradigm. It uses a trained Machine Learning model to act as a **Smart Safety Throttle**—evaluating a patient's physiological response to a moderate warmup and dynamically scaling their subsequent workout intensity (Low, Moderate, High) to keep them in a safe, therapeutic cardiovascular zone.

## System Architecture

The platform is built using a modern, decoupled architecture:

* **Backend:** FastAPI (RESTful API), SQLModel (ORM), SQLite.
* **Frontend:** Streamlit (Reactive UI), Plotly (Interactive Data Visualization).
* **Machine Learning:** XGBoost, Scikit-Learn, Pandas.
* **Domain:** Exercise Physiology, Cardiac Rehabilitation Protocols (Borg RPE Scale, HR Max Percentages).

## The "Smart Safety" Engine (Core Logic)

The crown jewel of this application is its dual-layer prescription engine, which perfectly balances deterministic medical rules with predictive machine learning.

### Layer 1: Deterministic Clinical Override

Before the ML model is allowed to make a prediction, the system checks for absolute clinical red flags. If a patient inputs dangerous vitals (e.g., Systolic BP > 160, Resting HR > 100) or experiences severe symptoms (Chest Pain, Dizziness, Borg Exertion $\ge$ 17), the system **bypasses the AI entirely**, immediately aborts the physical session, and prescribes a guided resting meditation.

### Layer 2: XGBoost Physiological Model

If the patient clears the safety layer, the backend feeds their post-warmup vitals into a pre-trained XGBoost pipeline (`best_model.pkl`). The model calculates complex features (like Pulse Change and Heart Rate as a percentage of Max HR) to determine their actual cardiovascular capacity:

* **The "Throttle Down" Rule (Low Intensity):** If the patient shows hidden signs of overexertion (e.g., HR spikes above 75% of Max HR during a simple warmup, or massive BP changes), the AI throttles their workout down to **Low** intensity, even if their subjective fatigue rating is low.
* **The "Baseline" Rule (Moderate Intensity):** Textbook, safe elevation of vitals results in a standard **Moderate** routine.
* **The "Scale Up" Rule (High Intensity):** Only if the patient proves they have massive cardiovascular reserve (HR remains $\le$ 70% of Max HR and Borg rating is $\le$ 12) will the AI clear them for a **High** intensity routine.

## Role-Based Features

### Patient Dashboard

* **Dynamic Session Flow:** Patients are guided through a clinical workflow: Pre-Workout Vitals $\rightarrow$ Warmup Prescription $\rightarrow$ Post-Warmup Feedback $\rightarrow$ AI Target Prescription.
* **Borg Scale Integration:** Utilizes the clinically validated Borg Rating of Perceived Exertion (RPE) scale (6-20) to capture subjective fatigue.
* **Vitals Trend Analysis:** Interactive Plotly charts mapping Heart Rate and Blood Pressure trends across historical sessions.
* **Continuous Monitoring:** A dedicated tab for live fitness tracking (HR, Steps) ingested from wearable APIs.

### Clinical Command Center (Doctor View)

* **Critical Alerts:** The dashboard automatically flags and filters urgent cases (patients who triggered the safety override) to the top for immediate review.
* **Patient Telemetry:** Deep dive into individual patient streaks, total caloric burn, and session-by-session vitals.
* **AI Override:** Doctors maintain ultimate authority. With a single click, a physician can override the AI's predicted intensity for any historical or upcoming session.
* **Clinical Remarks:** Ability to attach persistent medical notes to specific patient workout records.

## Data Models (SQLModel)

The relational database tracks a comprehensive set of patient data:

* **Pre-Workout Inputs:** Weight, Resting HR, Blood Pressure (Sys/Dia), Respiratory Rate, Pre-existing conditions (HTN, DM).
* **Calculated Metrics:** Maximum Heart Rate (MHR), Target HR Ranges, Caloric Burn (using MET multipliers).
* **Feedback Loop:** Post-warmup HR, Borg RPE, Mood, and String-matched Symptoms.