# Gemel Lehashkaa Analysis Tool

📊 **Investment Provident Fund (קופת גמל להשקעה) Simulator**

A comprehensive Streamlit web application for analyzing Israeli Investment Provident Fund savings scenarios, comparing different starting ages, and understanding the impact of fees and withdrawal modes.

## Features

- 📈 **Interactive Simulations** - Model your investment growth over time
- 🎂 **Start Age Comparisons** - See how starting earlier affects your final balance
- 💰 **Withdrawal Mode Analysis** - Compare lump sum (25% tax) vs tax-free annuity (age 60+)
- 📉 **Fee Impact Analysis** - Understand how management fees affect long-term growth
- 🔬 **Sensitivity Analysis** - Explore different return and fee scenarios with heatmaps
- 🇮🇱 **Israeli-Specific** - Implements actual Israeli tax laws and contribution caps

## Installation

### Prerequisites

- Python 3.9 or higher
- pip

### Setup

1. **Create virtual environment** (if not already created):
   ```bash
   python3 -m venv venv
   ```

2. **Install dependencies**:
   ```bash
   venv/bin/pip3 install -r requirements.txt
   ```

## Usage

### Running the App

```bash
venv/bin/streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### Key Parameters

Configure these in the sidebar:

- **Start Age** - When you begin contributing (18-59)
- **Withdrawal Age** - When you plan to withdraw (typically 60 for tax benefit)
- **Monthly Contribution** - Amount to contribute each month (₪)
- **Annual Cap** - Maximum yearly contributions (₪83,641 for 2026)
- **Expected Return** - Annual nominal return before fees (%)
- **AUM Fee** - Annual fee on assets under management (%)
- **Inflation** - For calculating real (inflation-adjusted) gains
- **Withdrawal Mode** - Lump sum or annuity conversion

## Model Details

### Tax Treatment

1. **Lump Sum Withdrawal**:
   - Taxed at 25% on **real gains** (inflation-adjusted)
   - Available at any age

2. **Annuity Conversion** (Age 60+):
   - **0% tax on gains** (recognized annuity)
   - Annuity payments are also tax-free
   - Requires transfer to pension-paying fund

### Formulas

**Monthly Balance Update**:
```
B_{t+1} = (B_t + D_t × (1 - F_d)) × (1 + r_m) × (1 - f_m)
```

Where:
- `B_t` = Balance at month t
- `D_t` = Deposit (respecting annual cap)
- `F_d` = Deposit fee
- `r_m` = Monthly return rate
- `f_m` = Monthly AUM fee

**Tax Calculation**:
```
Tax = 0.25 × max(B_T - Basis_real, 0)  [Lump sum]
Tax = 0                                  [Annuity after 60]
```

### Legal Caps (Israel 2026)

- Annual contribution cap: **₪83,641**
- Maximum AUM fee: **1.05%**
- Maximum deposit fee: **4%**
- Minimum age for tax-free annuity: **60**

## Project Structure

```
investment_provident_fund/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
└── src/
    ├── models.py               # Data models and constants
    ├── calculator.py           # Core calculation logic
    └── presentation/
        ├── inputs.py           # Sidebar input widgets
        ├── charts.py           # Plotly visualizations
        └── styles.py           # CSS and formatting
```

## Data Sources

- Based on **Amendment No. 15** to the Supervision of Financial Services (Provident Funds) Law
- Tax rates per Israeli Tax Authority guidelines
- Annual caps updated per CPI adjustments

## Disclaimer

⚠️ **This tool is for educational purposes only.**

The calculations and projections are based on assumptions and may not reflect actual future performance. Consult a licensed financial advisor for personalized advice.

## License

For personal use only.
