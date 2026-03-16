<div align="center">

# 🛡️ CreditGuard
### Retail Lending Risk Intelligence System

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.x-11557C?style=for-the-badge&logo=matplotlib&logoColor=white)](https://matplotlib.org)
[![SQL](https://img.shields.io/badge/SQL-Analytics-CC2927?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Status](https://img.shields.io/badge/Status-Complete-2ea44f?style=for-the-badge)](/)

> **End-to-end credit risk analytics pipeline** that transforms raw retail lending data into actionable risk intelligence — identifying default drivers, segmenting borrowers, and delivering data-backed policy recommendations that directly reduce Non-Performing Assets (NPAs).

</div>

---

## 📌 Business Problem

**GM Bank**, a mid-sized retail lending institution, experienced a surge in loan defaults following rapid portfolio expansion across personal loans, home loans, auto loans, and credit cards. Rising NPAs threatened portfolio health and regulatory standing.

**The challenge:** identify *which borrowers default, why they default, and when* — before it's too late.

---

## 🎯 Objectives

| # | Objective |
|---|-----------|
| 1 | Identify the key drivers influencing loan default |
| 2 | Segment customers by credit risk level (Low / Medium / High) |
| 3 | Detect repayment delinquency patterns and early warning signals |
| 4 | Evaluate risk exposure by product type and geographic region |
| 5 | Deliver actionable policy recommendations to reduce NPAs |

---

## 📊 Dataset

| Attribute | Detail |
|-----------|--------|
| **Records** | 1,500+ retail loan entries |
| **Source** | `RetailLendingRiskIntelligence.csv` |
| **Scope** | Historical loan data across all GM Bank retail products |

**Features analyzed:**

`customer_age` · `monthly_income` · `employment_type` · `credit_score` · `loan_amount` · `loan_tenure` · `emi_amount` · `emi_delay_days` · `loan_type` · `loan_status` · `region`

---

## 🏗️ Project Architecture

```
CreditGuard/
│
├── 📂 data/
│   ├── raw/                          # Source dataset (RetailLendingRiskIntelligence.csv)
│   └── processed/                    # Cleaned, analysis-ready data (clean_loans.csv)
│
├── 📂 src/
│   ├── load_data.py                  # Data ingestion & schema validation
│   ├── data_cleaning.py              # Missing value detection, deduplication, outlier IQR
│   ├── data_quality.py               # Pre-analysis data integrity checks
│   ├── eda_analysis.py               # Core risk analysis functions
│   ├── feature_engineering.py        # Derived feature construction
│   ├── visualization.py              # Chart generation (Matplotlib)
│   └── run_analysis.py               # Orchestration entrypoint
│
├── 📂 sql/
│   └── queries.sql                   # SQL-based risk queries
│
├── 📂 reports/
│   └── credit_risk_analysis_report.md  # Full narrative findings & recommendations
│
├── 📂 visuals/
│   ├── loan_type_default.png           # Default rate by product type
│   ├── credit_score_default.png        # Credit score vs. default correlation
│   ├── emi_delay_distribution.png      # EMI delay histogram
│   └── region_default.png             # Geographic default distribution
│
└── README.md
```

---

## ⚙️ Analytical Pipeline

```
Raw CSV → Load & Validate → Clean & QA → EDA → Feature Engineering → Visualize → Insights
```

### Stage 1 — Data Quality Validation
- Null detection across `monthly_income` and `credit_score` fields
- Duplicate identification by `loan_id` and `customer_id`
- IQR-based outlier flagging on `loan_amount`

### Stage 2 — Exploratory Data Analysis (EDA)
- **Default rate computation** — portfolio-level and segment-level
- **Income bracket segmentation** — Low / Lower-Middle / Upper-Middle / High Income
- **Age cohort analysis** — 18–30, 31–40, 41–50, 51–60, 60+
- **Employment type risk scoring** — salaried vs. self-employed vs. other
- **Credit score bucketing** — Low (300–600) / Medium (600–750) / High (750–900)

### Stage 3 — Risk Profiling & Segmentation
- Cross-tabulation of loan status against all key dimensions
- Default rate calculation per segment
- Three-tier risk classification: **Low · Medium · High**

### Stage 4 — Visualization
Four production-ready charts generated programmatically via Matplotlib:

| Chart | Insight |
|-------|---------|
| Default Rate by Loan Type | Product-level risk exposure |
| Credit Score vs. Default | Score band default probability |
| EMI Delay Distribution | Delinquency frequency patterns |
| Region-wise Default | Geographic concentration risk |

---

## 🔍 Key Findings

### 💳 Loan Default Assessment
- **Personal loans and credit cards** exhibit the highest default rates across the portfolio
- Default probability is significantly elevated in **lower income brackets**
- Unsecured loan products carry structurally higher risk than secured counterparts

### 👤 Customer Risk Profiling
- **Low credit score borrowers (300–600)** are the primary NPA contributors
- **Unstable employment types** correlate with elevated repayment failure
- Risk segmentation enables targeted intervention at each borrower tier

### 📅 Repayment & Delinquency Signals
- **Frequent EMI delays** are the strongest leading indicator of eventual default
- Long-tenure loans demonstrate compounding delinquency risk over time
- Borrowers with **multiple active loans** show measurable repayment stress

### 🗺️ Regional & Product Risk
- Geographic default concentration identified in specific high-risk regions
- Unsecured product lines consistently underperform secured counterparts in repayment

---

## 💡 Business Recommendations

| Priority | Recommendation |
|----------|----------------|
| 🔴 High | Tighten credit approval criteria for sub-600 credit score applicants |
| 🔴 High | Implement EMI affordability caps as a percentage of verified monthly income |
| 🟠 Medium | Deploy early warning dashboards triggered by consecutive EMI delays |
| 🟠 Medium | Increase monitoring frequency for flagged high-risk regions |
| 🟡 Standard | Revise pricing and approval thresholds for unsecured loan products |

---

## 🚀 Getting Started

### Prerequisites
```bash
Python >= 3.8
```

### Installation
```bash
# Clone the repository
git clone https://github.com/Umangmojidra/creditguard.git
cd creditguard

# Install dependencies
pip install pandas numpy matplotlib
```

### Run the Analysis
```bash
# Run full pipeline
python src/run_analysis.py
```

Outputs will be saved to `visuals/` and findings documented in `reports/credit_risk_analysis_report.md`.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.12** | Core analysis language |
| **Pandas** | Data manipulation, cross-tabulation, segmentation |
| **NumPy** | Statistical computations, IQR outlier detection |
| **Matplotlib** | Chart generation and visualization |
| **SQL** | Supplementary analytical queries |

---

## 📈 Skills Demonstrated

- ✅ End-to-end data analytics pipeline design
- ✅ Financial domain knowledge (credit risk, NPA, delinquency, EMI)
- ✅ Data quality validation and anomaly detection
- ✅ Multi-dimensional customer segmentation
- ✅ Insight-to-recommendation translation for business stakeholders
- ✅ Modular, production-style Python code organization
- ✅ Data visualization with business storytelling

---

## 📄 Full Report

The complete analysis with all findings, methodology, and recommendations is available in:

📋 [`reports/credit_risk_analysis_report.md`](reports/credit_risk_analysis_report.md)

---

## 👤 Author

** Umang Mojidra **
Data Analyst | Risk Analytics | Financial Intelligence

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/umangmojidra)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/Umangmojidra)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=flat&logo=gmail)](mailto:mojidraumang345@email.com)

---

<div align="center">

*Built to turn raw lending data into risk intelligence that protects portfolio health.*

</div>