Here is the full English translation of your text:

---

# Comprehensive Guide to an Investment Provident Fund (Kupat Gemel Lehashka’a) in Israel for Building an Optimization Model for the Deposit Start Age

## Executive Summary

An Investment Provident Fund is a designated “provident fund” created by legislation (Amendment No. 15 to the Supervision of Financial Services (Provident Funds) Law), defined as a fund intended to pay a capital sum to a member (specifically: an “independent member”) or to their beneficiaries.

### Contributions

There is an annual contribution cap per individual. The law sets a base of NIS 70,000 per tax year, with an annual update mechanism on January 1 according to the increase in the Consumer Price Index known on that date.

In practice, managing institutions publish updated caps such as:

* NIS 81,711.88 for 2025
* NIS 83,641 (or 83,641.09) for 2026

The cap applies to the total contributions across all Investment Provident Fund accounts of the same saver, even if held with different institutions.

### Liquidity

Funds are fully liquid and may be withdrawn in full or in part at any time. A common standard regulation provides that the managing company must pay accumulated funds within 4 business days of receiving a complete and signed request, with a possible technical delay to the fourth business day if the payment date falls at the beginning of the month.

### Taxation

There is no tax benefit at the contribution stage.

A lump-sum withdrawal is generally taxed at 25% capital gains tax on real (inflation-adjusted) gains.

From age 60, funds may be converted into an annuity. In that case, a tax exemption applies to accumulated gains and to the full annuity (“recognized annuity”), usually via transfer to a pension-paying fund.

### Management Fees

Regulations set maximum fees of:

* Up to 1.05% annually from accumulated assets
* Up to 4% from contributions
* For annuity recipients: a dedicated cap of 0.6% annually

In practice, market averages often show management fees from assets around ~0.55%–0.65% in leading funds (example: “General” track in 2025), and contribution fees are often 0% (depending on institution/channel).

---

Below is a computational model (formulas + pseudocode + scenario charts) that enables simulation for different starting ages (e.g., 30/40/50/59/60), with parameters for return, inflation, contribution cap, management fees, and tax — and allows searching for an optimum under defined assumptions.

---

# Legal Framework and Definitions

The main normative basis is Amendment No. 15 (2016) to the Supervision of Financial Services (Provident Funds) Law. This amendment introduced the definition:

“Investment Provident Fund” — a provident fund intended to pay a capital amount to an independent member or their beneficiaries.

The amendment also embedded the annual contribution cap in Section 22 of the law, including the CPI update mechanism.

### Eligibility / Opening

At the public right level, it is described that an Investment Provident Fund can be opened for a person at any age.

Standard regulations commonly reference accounts for minor children, stating that the managing company may pay funds from a “minor child’s account” if requested by their legal guardian. This reinforces the interpretation that accounts can be managed in the name of a minor (subject to institutional procedures and law).

---

# Summary Table of Legal Milestones and Thresholds

| Topic                          | Threshold / Rule                                | Modeling Implication                                                             |
| ------------------------------ | ----------------------------------------------- | -------------------------------------------------------------------------------- |
| Legal Definition               | Investment fund intended to pay capital sum     | Accumulation product allowing lump-sum withdrawal; annuity optional via transfer |
| Annual Contribution Cap        | NIS 70,000 base, CPI-linked annually            | Annual per-person contribution constraint required                               |
| Cap Enforcement                | Checked at time of deposit                      | Algorithm must block excess deposits in real time                                |
| Liquidity                      | Payment within 4 business days                  | No lock-up period                                                                |
| Legal Fee Caps                 | 1.05% AUM; 4% deposit; 0.6% annuity             | Fee validation constraints                                                       |
| Tax Benefit Age                | From 60 – annuity transfer allows tax exemption | Decision trigger: lump sum vs tax-free annuity                                   |
| Historical Temporary Provision | Special 2017 exception                          | Edge case only                                                                   |

---

# Contribution Rules and Caps

The annual contribution cap is central to the model.

The law states that total payments a member may deposit across all Investment Provident Fund accounts shall not exceed NIS 70,000 per tax year, CPI-adjusted annually on January 1.

### Operational Detail

A common regulation states that compliance with the cap is checked at the time of deposit — not only at year-end.

Implication: Monthly deposits must be automatically truncated when the cap is reached.

There is no separate monthly cap — the restriction is annual.

---

# Taxation and Withdrawals

## Liquidity

Funds are liquid at any time. No exit penalty applies, but capital gains tax may apply.

Standard SLA: payment within four business days.

---

## Lump-Sum Withdrawal

Capital gains tax of up to 25% on real gains (inflation-adjusted profit).

If the saver’s marginal tax rate is below 25%, a tax refund may be possible. The model should therefore allow an “effective_tax_rate” parameter.

---

## 0% Capital Gains Tax via Annuity (After Age 60)

A significant benefit:

If the saver reaches age 60 and converts funds into a monthly annuity instead of a lump sum:

* Gains are exempt from capital gains tax
* The annuity itself is tax-free (“recognized annuity”)

Process: transfer to a pension-paying fund.

Important distinction:

1. Lump sum (any age): 25% tax on real gains
2. Lump sum after 60: still taxed
3. Annuity after 60: 0% tax on gains

Partial lump sum + partial annuity is possible — exemption applies only to the annuity portion.

---

## Clarification Regarding 15% Tax

The 15% nominal gains tax example often refers to other products (e.g., Amendment 190 funds), not the standard Investment Provident Fund.

Default modeling assumptions:

* Lump sum: 25% on real gains
* Annuity after 60: 0% on gains

---

# Management Fees

## Legal Caps

* 1.05% annually from assets
* 4% from contributions
* 0.6% annually for annuity recipients

System validation should enforce these limits.

---

## Market Practice

Common structure:

* AUM-based fee
* Sometimes contribution fee (often 0%)

Example (digital channel): 0.75% AUM only.

Market averages (2025 general track example): ~0.55%–0.65%.

Modeling recommendation: simulate Low/Med/High fee scenarios.

---

## Investment Management Expenses

Beyond contractual fees, there are embedded investment expenses (trading costs, external management fees). These should be modeled as an additional annual drag (e.g., 0.1%–0.3%).

---

# Computational Model

## Recommended Parameters

* Start age (A_s)
* Withdrawal age (A_w)
* Monthly contribution (C_m)
* Annual cap (Cap_y)
* Expected annual return (R)
* Annual AUM fee (F_a)
* Deposit fee (F_d)
* Inflation (π)
* Capital gains tax rate (τ)
* withdrawal_mode = lump / annuity

---

## Monthly Conversions

[
r_m = (1+R)^{1/12} - 1
]

[
f_m \approx \frac{F_a}{12}
]

[
\pi_m = (1+\pi)^{1/12} - 1
]

---

## Monthly Balance Update

[
B_{t+1} = (B_t + D_t(1 - F_d)) (1+r_m)(1-f_m)
]

Where (D_t) respects annual cap.

---

## Tax Calculation (Lump Sum)

[
Tax = \tau \cdot \max(B_T - Basis^{real}_T, 0)
]

Real basis:

[
Basis^{real}_T = \sum D_t (1+\pi_m)^{(T-t)}
]

If annuity after 60:

[
Tax = 0
]

---

## Pseudocode

(Original pseudocode preserved conceptually in English)

```
function simulate(...):
    B = 0
    basis_indexed = 0

    for each month:
        enforce annual cap
        apply deposit fee
        update indexed basis
        apply return and AUM fee

    if annuity and age >= 60:
        tax = 0
    else:
        tax = tax_rate * real_gain

    return gross, tax, net
```

---

# General Modeling Conclusion: When Is It Optimal to Start?

Under positive expected net returns and/or annuity tax benefit after age 60:

Earlier starting age generally results in higher accumulated balance at the target age, due to:

* Earlier contributions
* Longer compounding

However, a robust model must test:

* Low/negative return scenarios
* High fee scenarios
* Early liquidity needs (pre-60 lump sum)

Separate decision paths should be modeled:

* Likely lump sum withdrawal
* Explicit intent to convert to annuity

---

# Implementation Guidance

Recommended inputs:

* start_age, withdraw_age
* contribution schedule
* annual_cap_by_year
* fee parameters
* extra expenses
* return model
* inflation model
* withdrawal_mode
* tax model

Recommended outputs:

* Gross balance
* Total contributions
* Estimated tax
* Net balance
* Time series
* Cap binding flags

---

# Edge Cases

* Legal fee cap validation
* Aggregation across multiple accounts
* Mid-year start (cap is annual, not pro-rata)
* Mixed withdrawal (partial annuity)
* Post-annuity restrictions
* Inflation modeling accuracy
* 2017 historical exception

---

# Uncertainties and Modeling Assumptions

* Annual cap varies yearly (must be input dynamically)
* Effective tax may vary by individual
* Fees are negotiable
* Investment expenses vary
* 2017 exception applies only to legacy accounts

---

If you'd like, I can also provide a condensed executive-only version, a technical modeling-only version, or a clean academic-style English rewrite suitable for publication.
