# Data Sources

All facility power figures are sourced from publicly available records. No proprietary data is used.

## Facility Power

| Facility | MW | Source | URL |
|---|---|---|---|
| Google Council Bluffs IA | 602 | Baxtel facility tracker | baxtel.com |
| Google The Dalles OR | 80 | Baxtel Oregon market (Dalles 5) | baxtel.com |
| Google Ashburn VA | 100 | Interconnection.fyi permit record | interconnection.fyi |
| AWS Ashburn VA | 202.7 | Datacenter.fyi Amazon Data Services permit, Dominion Energy grid | datacenter.fyi |
| AWS Hilliard OH | 60 | Baxtel Cosgray Campus; AEP fuel cell permit for 73 MW confirms scale | baxtel.com |
| Meta DeKalb IL | 40 | Interconnection.fyi: 25-50 MW range, midpoint used | interconnection.fyi |
| Meta Prineville OR | 112 | Data Center Dynamics: 982,177 MWh annual usage | datacenterdynamics.com |
| Meta Altoona IA | 142 | Data Center Dynamics: 1,243,306 MWh annual usage | datacenterdynamics.com |
| Microsoft Boydton VA | 412.5 | Datacenter.fyi public permit, operational April 2024 | datacenter.fyi |
| Microsoft Quincy WA | 150 | Campus estimate from 800,000 sqft + historical permit data | datacenterknowledge.com |
| CoreWeave Plano TX | 120 | CoreWeave/Nvidia press release, $1.6B facility, 3,500+ H100s | coreweave.com |
| CoreWeave Lancaster PA | 100 | CoreWeave press release July 2025, expandable to 300 MW | coreweave.com |
| Nebius Mantsala Finland | 75 | Nebius press release October 2024: tripled capacity | nebius.com |
| Nebius Kansas City MO | 35 | Nebius 2025 US expansion announcement | nebius.com |
| Scaleway PAR-DC5 Paris | 30 | Scaleway Environmental Leadership page 2024 | scaleway.com |

## PUE Values

| Provider | PUE | Source |
|---|---|---|
| Google | 1.09 | Google 2024 Environmental Report |
| Meta | 1.08 | Meta 2024 Environmental Data Report |
| AWS | 1.15 | AWS Sustainability Report 2024 |
| Microsoft Azure | 1.16 | Microsoft CSR 2024 |
| Nebius | 1.10 | Nebius SEC 6-K FY2024, Finland Mantsala site |
| Scaleway | 1.30 (midpoint) | Scaleway Environmental Leadership 2024: 1.37 fleet avg, 1.25 AI cluster |
| CoreWeave | 1.35 (estimated) | Not publicly disclosed. Modeled as mid-tier colo. |
| Industry average | 1.56 | Uptime Institute Global Data Center Survey 2024 |

## CPU Mix

| Provider | Source |
|---|---|
| ARM share (all providers) | ARM Holdings SEC 6-K FY2024/FY2025 |
| Hyperscaler mix | Dell'Oro Group Q2 2025 Data Center IT CapEx Report |
| Market share | Mercury Research Q3 2024 server CPU share data |
| Google Axion deployment | Google Cloud Blog, October 2024 |
| AWS Graviton scale | ARM Holdings 6-K: 50,000+ customers, doubled YoY |
| Azure Cobalt + custom EPYC | Microsoft Ignite 2024 |

## Utilization Rates

| Source | Finding |
|---|---|
| Lawrence Berkeley National Lab 2024 US Data Center Energy Report | Hyperscalers at highest utilization tier |
| Uptime Institute Global Data Center Survey 2024 (670 operators) | 1 in 4 DCs below 40% UPS utilization |
| Duke Energy 2024 NC Utilities Commission testimony | 90% load factor for large DCs |

## TDP Reference

| CPU | TDP | Source |
|---|---|---|
| Intel Xeon Granite Rapids 6980P | 500W | Phoronix benchmark review, September 2024 |
| Intel Xeon Sapphire Rapids 8462Y+ | 300W | Intel ARK database |
| AMD EPYC Genoa/Turin | 280-360W | AMD product specifications |
| ARM Graviton/Axion/Cobalt | ~75W est. | ARM Holdings efficiency disclosures |

## CapEx Sources (Forecast Page)

| Provider | Source |
|---|---|
| Google $52.5B (2024), $75B (2025) | Platformonomics Follow the CapEx 2024 Retrospective, Alphabet SEC filings |
| AWS $53.3B DC (2024), $67B (2025) | Platformonomics: 64% of Amazon $83.9B total attributed to AWS |
| Meta $39B (2024), $65B (2025) | PREA Spring 2025 Quarterly, Meta SEC filings |
| Microsoft $44B (2024), $80B (2025) | PREA Spring 2025 Quarterly, Microsoft SEC filings |
| CoreWeave $14B (2025), $30-35B (2026 guided) | CoreWeave Q4 2025 earnings, FY2025 annual report |
| Nebius $2B (2025), $16-20B (2026 guided) | Nebius Q1 2025 earnings, DCD reporting |
| GPU share of server spend | Dell'Oro Group Q3-Q4 2024 (36-40%); Goldman Sachs 2026 ($180B of $450B) |
