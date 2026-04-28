# DC-Capacity-Model
Reverse-engineer CPU capacity from public signals

# Dark Capacity: Reverse-Engineering Global Data Center Compute

How much compute does a hyperscaler actually run? Nobody publishes that number. We built a model to estimate it from public data.

Read the full breakdown → (darkcapacity.gargeenimdeo.com/writeup)

# What this is

Data centers publish almost nothing about the servers inside them. But they do file utility permits, publish PUE scores in sustainability reports, and disclose CPU architecture decisions in earnings calls and technical blogs.

We reverse-engineered CPU socket counts for 25 facilities across 15 providers — Google, AWS, Meta, Microsoft, CoreWeave, Nebius, and others, using a formula chain built entirely from public sources:

Facility Power (MW) → IT Load (÷ PUE) → Effective Load (× Utilization)
→ Blended TDP (Intel / AMD / ARM mix) → CPU Socket Estimate

The model outputs a point estimate with a ±25% confidence range. We cross-validated against an independent data center simulator and landed within 1.7% on Google's The Dalles facility.

# Methodology in brief

Power data: sourced from utility permit filings, state environmental disclosures, press releases, and sustainability reports. Where a range was reported, we used the midpoint.

PUE: taken from provider sustainability reports where published (Google: 1.09, Meta: 1.08). For providers without public PUE, we used tier-appropriate industry benchmarks.

CPU architecture mix: inferred from public technical blog posts, conference talks, earnings call transcripts, and procurement announcements. Google and AWS are modeled at 55-60% ARM, given public Axion and Graviton disclosures.

TDP assumptions: Intel Sapphire Rapids: 300W, AMD EPYC Genoa: 320W, ARM (Graviton/Axion class): 75W. Blended by the provider architecture mix.

Utilization: 85% for hyperscalers, lower for colocation and telco facilities, based on industry benchmarks.

# Validation

We modeled Google The Dalles B1 in [dc-simulator-omega.vercel.app](https://dc-simulator-omega.vercel.app): 8 halls, 3,336 racks, 30 kW/rack, Hyperscale profile. Simulator output: 122.08 MW. Our model estimate: 120 MW. Delta: 1.7%.

# Authors

Gargee Nimdeo: Data and BI Engineering · [LinkedIn](https://linkedin.com/in/gargee-nimdeo) · [GitHub](https://github.com/Gargee77)
KG Sriram: Product Marketing Manager · [LinkedIn](https://www.linkedin.com/in/kg-sriram/) · [GitHub](https://github.com/kgs222)
Sandeep Vangara: Supply Chain Manager · [LinkedIn](https://www.linkedin.com/in/sandeepvangara/) · [GitHub](https://github.com/lordSauron1710)

*Data sourced from public filings, sustainability reports, and press releases. CPU estimates carry a ±25% range. This is an estimation exercise, not an audit.*
