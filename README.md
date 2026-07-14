glioblastoma-clinical-trial-intelligence-platform
An interactive healthcare analytics platform developed using publicly available ClinicalTrials.gov glioblastoma clinical trial data. The platform integrates Python, Streamlit, and Power BI to transform large-scale clinical trial data into actionable oncology research intelligence for data exploration, visualization, and research analytics.
## Project Overview

Glioblastoma is one of the most aggressive primary brain tumors, with numerous clinical trials investigating new therapies, biomarkers, and treatment strategies. This project demonstrates how publicly available clinical trial data can be processed and transformed into an interactive clinical intelligence platform to support healthcare analytics and evidence-based research.

---

## Features

### Executive Dashboard

- Total Clinical Trials
- Completed Trials
- Ongoing Trials
- Stopped / Failed Trials
- Countries Represented
- Median Enrollment
- Trial Outcome Distribution
- Clinical Trial Trend
- Phase Distribution
- Sponsor Classification

### Clinical Trial Explorer

- Search clinical trials
- Filter by Status
- Filter by Phase
- Filter by Sponsor
- Filter by Country
- Interactive trial table
- CSV download

### Research Intelligence

- Failure Intelligence
- Drug Intelligence
- Biomarker Intelligence
- Combination Therapy Intelligence
- Research Opportunity Analysis

### AI Research Assistant

- Drug summary
- Biomarker summary
- Failure insights
- Opportunity insights
- Interactive question answering

---

## Technologies Used

- Python
- Streamlit
- Pandas
- Plotly
- Power BI
- ClinicalTrials.gov
- Healthcare Analytics

---

## Project Structure

```
Glioblastoma_Clinical_Trial_Intelligence_Platform
│
├── app.py
├── requirements.txt
├── README.md
│
├── data
│   ├── all_glioblastoma_trials.csv
│   ├── basic_stats.csv
│   ├── status_summary.csv
│   ├── phase_summary.csv
│   ├── sponsor_summary.csv
│   ├── intervention_name_summary.csv
│   ├── country_summary.csv
│   ├── failure_intelligence.csv
│   ├── drug_intelligence.csv
│   ├── biomarker_intelligence.csv
│   ├── combination_intelligence.csv
│   └── opportunity.csv
│
├── notebooks
│   └── Glioblastoma_Clinical_Trial_Intelligence.ipynb
│
├── powerbi
│   └── Glioblastoma_Clinical_Trial_Intelligence.pbix
│
└── screenshots
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/fniraj/glioblastoma-clinical-trial-intelligence-platform.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run app.py
```

---

## Dashboard Preview

### Executive Dashboard

<img src="screenshots/dashboard.png" width="100%">

### Clinical Trial Explorer

<img src="screenshots/explorer.png" width="100%">

### Research Intelligence

<img src="screenshots/intelligence.png" width="100%">

### AI Research Assistant

<img src="screenshots/assistant.png" width="100%">

---

## Data Source

ClinicalTrials.gov

https://clinicaltrials.gov

---

## Disclaimer

This project is developed for educational, research, and healthcare analytics purposes using publicly available clinical trial data. It is not intended for clinical decision-making or medical advice.

---

## Author

**Niraj**

MS Health Informatics

Michigan Technological University

GitHub: https://github.com/fniraj

LinkedIn: https://www.linkedin.com/in/fniraj/
