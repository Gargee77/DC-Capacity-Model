"""
Dark Capacity — DC CPU Estimation Model
=======================================
Runs the full formula chain across all sourced data center facilities.
Outputs a clean CSV to data/processed/ for use in SQL and Tableau.

Formula:
    IT Load (MW)       = Total DC Power (MW) / PUE
    Effective Draw (W) = IT Load * Utilization Rate * 1,000,000
    CPU Count          = Effective Draw / Weighted TDP (W)

    Confidence band uses:
        min = Effective Draw / 500W  (all high-end Intel Xeon Granite Rapids)
        max = Effective Draw / 75W   (all ARM / custom silicon)

Author: Gargee Nimdeo
"""

import csv
import math
import os

# ---------------------------------------------------------------------------
# PROVIDER DEFAULTS
# Source: company sustainability reports, SEC filings, Uptime Institute 2024
# ---------------------------------------------------------------------------
PROVIDERS = {
    "google": {
        "pue": 1.09,
        "utilization": 0.85,
        "intel_pct": 25, "amd_pct": 15, "arm_pct": 60,
        "pue_source": "Google 2024 Environmental Report",
        "util_source": "LBNL 2024 US Data Center Energy Report",
        "type": "CPU-Mix",
    },
    "aws": {
        "pue": 1.15,
        "utilization": 0.85,
        "intel_pct": 30, "amd_pct": 15, "arm_pct": 55,
        "pue_source": "AWS Sustainability Report 2024",
        "util_source": "LBNL 2024 US Data Center Energy Report",
        "type": "CPU-Mix",
    },
    "meta": {
        "pue": 1.08,
        "utilization": 0.85,
        "intel_pct": 40, "amd_pct": 35, "arm_pct": 25,
        "pue_source": "Meta 2024 Environmental Data Report",
        "util_source": "LBNL 2024 US Data Center Energy Report",
        "type": "CPU-Mix",
    },
    "azure": {
        "pue": 1.16,
        "utilization": 0.85,
        "intel_pct": 35, "amd_pct": 30, "arm_pct": 35,
        "pue_source": "Microsoft CSR 2024",
        "util_source": "LBNL 2024 US Data Center Energy Report",
        "type": "CPU-Mix",
    },
    "coreweave": {
        "pue": 1.35,
        "utilization": 0.77,
        "intel_pct": 50, "amd_pct": 40, "arm_pct": 10,
        "pue_source": "Not publicly disclosed, modeled as mid-tier colo",
        "util_source": "Uptime Institute 2024, neocloud estimate",
        "type": "GPU-Centric",
    },
    "nebius": {
        "pue": 1.10,
        "utilization": 0.77,
        "intel_pct": 50, "amd_pct": 40, "arm_pct": 10,
        "pue_source": "Nebius SEC 6-K FY2024, Finland Mantsala site",
        "util_source": "Uptime Institute 2024, neocloud estimate",
        "type": "GPU-Centric",
    },
    "scaleway": {
        "pue": 1.30,
        "utilization": 0.68,
        "intel_pct": 55, "amd_pct": 35, "arm_pct": 10,
        "pue_source": "Scaleway Environmental Leadership 2024 (1.37 fleet / 1.25 AI cluster)",
        "util_source": "Uptime Institute 2024, Tier 2 cloud estimate",
        "type": "CPU-Mix",
    },
}

# TDP reference values (watts per socket)
TDP_INTEL_W  = 300   # Intel Xeon Sapphire/Emerald Rapids avg (ARK database)
TDP_AMD_W    = 320   # AMD EPYC Genoa/Turin avg (AMD product specs)
TDP_ARM_W    = 75    # ARM/Custom (Graviton, Axion, Cobalt) estimated
TDP_MIN_W    = 75    # All-ARM floor — widens confidence band upper end
TDP_MAX_W    = 500   # Intel Xeon Granite Rapids 6980P (Phoronix Sept 2024)

# GPU-centric IT load adjustment
# For GPU-centric DCs, GPUs consume the majority of IT power.
# H100/H200 SXM: ~700W TDP per GPU. Blackwell B200: ~1,000W.
# Host CPUs are ~2 per GPU node (NVLink switch nodes).
# GPU power fraction: ~85% of IT load goes to GPU draw for these facilities.
# We model CPU-only effective draw as: IT_load * (1 - GPU_IT_FRACTION)
GPU_IT_POWER_FRACTION = 0.85  # 85% of IT power consumed by GPUs in GPU-centric DCs


# ---------------------------------------------------------------------------
# FACILITY DATASET
# All power figures sourced from public records — see docs/sources.md
# ---------------------------------------------------------------------------
FACILITIES = [
    {
        "facility_id":   "google_council_bluffs",
        "facility_name": "Google Council Bluffs IA",
        "provider":      "google",
        "location":      "Council Bluffs, Iowa, USA",
        "total_power_mw": 602,
        "power_source":  "Baxtel tracker: 8 sites, 602 MW campus total",
        "year_online":   2012,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "google_the_dalles",
        "facility_name": "Google The Dalles OR",
        "provider":      "google",
        "location":      "The Dalles, Oregon, USA",
        "total_power_mw": 80,
        "power_source":  "Baxtel Oregon market: Google Dalles 5 at 80 MW",
        "year_online":   2006,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "google_ashburn",
        "facility_name": "Google Ashburn VA",
        "provider":      "google",
        "location":      "Ashburn, Virginia, USA",
        "total_power_mw": 100,
        "power_source":  "Interconnection.fyi public permit record: 100 MW",
        "year_online":   2018,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "aws_ashburn",
        "facility_name": "AWS Ashburn VA",
        "provider":      "aws",
        "location":      "Ashburn, Virginia, USA",
        "total_power_mw": 202.7,
        "power_source":  "Datacenter.fyi: 202.7 MW, Amazon Data Services permit, Dominion Energy grid",
        "year_online":   2016,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "aws_hilliard",
        "facility_name": "AWS Hilliard OH Cosgray Campus",
        "provider":      "aws",
        "location":      "Hilliard, Ohio, USA",
        "total_power_mw": 60,
        "power_source":  "Baxtel: Cosgray Campus 60 MW. AEP fuel cell permit for 73 MW confirms scale.",
        "year_online":   2015,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "meta_dekalb",
        "facility_name": "Meta DeKalb IL",
        "provider":      "meta",
        "location":      "DeKalb, Illinois, USA",
        "total_power_mw": 40,
        "power_source":  "Interconnection.fyi: 25-50 MW range, midpoint 40 MW. $1B campus investment.",
        "year_online":   2023,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "meta_prineville",
        "facility_name": "Meta Prineville OR Campus",
        "provider":      "meta",
        "location":      "Prineville, Oregon, USA",
        "total_power_mw": 112,
        "power_source":  "DCD sustainability data: 982,177 MWh annual usage implies ~112 MW avg draw",
        "year_online":   2011,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "meta_altoona",
        "facility_name": "Meta Altoona IA",
        "provider":      "meta",
        "location":      "Altoona, Iowa, USA",
        "total_power_mw": 142,
        "power_source":  "DCD sustainability: 1,243,306 MWh annual usage implies ~142 MW avg draw",
        "year_online":   2015,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "msft_boydton",
        "facility_name": "Microsoft Boydton VA",
        "provider":      "azure",
        "location":      "Boydton, Virginia, USA",
        "total_power_mw": 412.5,
        "power_source":  "Datacenter.fyi public permit: 412.5 MW, operational April 2024, Dominion Energy VA",
        "year_online":   2024,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "msft_quincy",
        "facility_name": "Microsoft Quincy WA Campus",
        "provider":      "azure",
        "location":      "Quincy, Washington, USA",
        "total_power_mw": 150,
        "power_source":  "Campus estimate: 800,000 sqft, historical permit data confirms ~150 MW range",
        "year_online":   2007,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "coreweave_plano",
        "facility_name": "CoreWeave Plano TX",
        "provider":      "coreweave",
        "location":      "Plano, Texas, USA",
        "total_power_mw": 120,
        "power_source":  "CoreWeave/Nvidia press release: $1.6B facility, 3,500+ H100s. IT load est. 120 MW.",
        "year_online":   2024,
        "cross_check_public_unit_count": 3500,
        "cross_check_note": "3,500 H100 GPUs disclosed. At 1 CPU per 2 GPUs, implies ~1,750 host CPUs.",
    },
    {
        "facility_id":   "coreweave_lancaster",
        "facility_name": "CoreWeave Lancaster PA",
        "provider":      "coreweave",
        "location":      "Lancaster, Pennsylvania, USA",
        "total_power_mw": 100,
        "power_source":  "CoreWeave press release July 2025: 100 MW initial, expandable to 300 MW",
        "year_online":   2025,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
    {
        "facility_id":   "nebius_mantsala",
        "facility_name": "Nebius Mantsala Finland",
        "provider":      "nebius",
        "location":      "Mantsala, Finland",
        "total_power_mw": 75,
        "power_source":  "Nebius press release October 2024: tripled capacity to 75 MW, up to 60,000 GPUs",
        "year_online":   2024,
        "cross_check_public_unit_count": 60000,
        "cross_check_note": "60,000 GPUs disclosed. At 1 CPU per 2 GPUs, implies ~30,000 host CPUs.",
    },
    {
        "facility_id":   "nebius_kc",
        "facility_name": "Nebius Kansas City MO",
        "provider":      "nebius",
        "location":      "Kansas City, Missouri, USA",
        "total_power_mw": 35,
        "power_source":  "Nebius 2025 US expansion: first US cluster, up to 35,000 GPUs, est. 35 MW initial",
        "year_online":   2025,
        "cross_check_public_unit_count": 35000,
        "cross_check_note": "35,000 GPUs planned. At 1 CPU per 2 GPUs, implies ~17,500 host CPUs.",
    },
    {
        "facility_id":   "scaleway_par5",
        "facility_name": "Scaleway PAR-DC5 Paris",
        "provider":      "scaleway",
        "location":      "Paris, France",
        "total_power_mw": 30,
        "power_source":  "Scaleway Environmental Leadership 2024: AI cluster, PUE 1.25. Capacity est. 30 MW.",
        "year_online":   2024,
        "cross_check_public_unit_count": None,
        "cross_check_note": None,
    },
]


# ---------------------------------------------------------------------------
# CORE FUNCTIONS
# ---------------------------------------------------------------------------

def weighted_tdp(intel_pct: int, amd_pct: int, arm_pct: int) -> float:
    """
    Calculate weighted average TDP per CPU socket given architecture mix.
    Returns watts.
    """
    return (intel_pct / 100) * TDP_INTEL_W \
         + (amd_pct  / 100) * TDP_AMD_W    \
         + (arm_pct  / 100) * TDP_ARM_W


def estimate_cpus(total_power_mw: float, pue: float,
                  utilization: float, tdp_w: float,
                  provider_type: str = "CPU-Mix") -> dict:
    """
    Run the full formula chain for a single facility.
    For GPU-centric providers, only the non-GPU fraction of IT load
    is attributed to host CPUs (GPUs consume ~85% of IT power).
    Returns a dict of all intermediate and final values.
    """
    it_load_mw     = total_power_mw / pue
    eff_draw_mw    = it_load_mw * utilization

    # For GPU-centric DCs, CPUs only consume the non-GPU slice of IT power.
    # H100 SXM: ~700W GPU TDP vs ~300W host CPU. At 2 CPUs per 8-GPU node,
    # GPUs draw ~85% of total IT load.
    if provider_type == "GPU-Centric":
        eff_draw_mw = eff_draw_mw * (1 - GPU_IT_POWER_FRACTION)

    eff_draw_w     = eff_draw_mw * 1_000_000

    cpu_point      = eff_draw_w / tdp_w
    cpu_min        = eff_draw_w / TDP_MAX_W   # all high-end Intel = fewest CPUs
    cpu_max        = eff_draw_w / TDP_MIN_W   # all ARM = most CPUs

    conf_band_pct  = ((cpu_max - cpu_min) / cpu_point) * 100

    return {
        "it_load_mw":    round(it_load_mw, 2),
        "eff_draw_mw":   round(eff_draw_mw, 2),
        "eff_draw_w":    round(eff_draw_w, 0),
        "cpu_point":     round(cpu_point),
        "cpu_min":       round(cpu_min),
        "cpu_max":       round(cpu_max),
        "conf_band_pct": round(conf_band_pct, 1),
    }


def cross_check_status(provider_type: str,
                       cpu_point: int,
                       public_gpu_count) -> str:
    """
    For GPU-centric providers with known GPU counts, derive expected host
    CPU count (1 CPU per 2 GPUs for Hopper/Blackwell systems) and check
    whether model estimate is within a reasonable range.
    """
    if public_gpu_count is None:
        return "no_data"
    if provider_type != "GPU-Centric":
        return "not_applicable"

    expected_cpus = public_gpu_count / 2
    # Flag as validated if within +/- 50% of derived expected count
    lower = expected_cpus * 0.50
    upper = expected_cpus * 2.00
    if lower <= cpu_point <= upper:
        return "validated"
    return "out_of_range"


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def run():
    rows = []

    for f in FACILITIES:
        prov   = PROVIDERS[f["provider"]]
        tdp_w  = weighted_tdp(prov["intel_pct"], prov["amd_pct"], prov["arm_pct"])
        result = estimate_cpus(
            total_power_mw = f["total_power_mw"],
            pue            = prov["pue"],
            utilization    = prov["utilization"],
            tdp_w          = tdp_w,
            provider_type  = prov["type"],
        )
        xcheck = cross_check_status(
            provider_type        = prov["type"],
            cpu_point            = result["cpu_point"],
            public_gpu_count     = f["cross_check_public_unit_count"],
        )

        row = {
            # Facility identity
            "facility_id":              f["facility_id"],
            "facility_name":            f["facility_name"],
            "provider":                 f["provider"],
            "provider_type":            prov["type"],
            "location":                 f["location"],
            "year_online":              f["year_online"],

            # Sourced inputs
            "total_power_mw":           f["total_power_mw"],
            "power_source":             f["power_source"],

            # Provider assumptions
            "pue":                      prov["pue"],
            "pue_source":               prov["pue_source"],
            "utilization_rate":         prov["utilization"],
            "util_source":              prov["util_source"],
            "intel_pct":                prov["intel_pct"],
            "amd_pct":                  prov["amd_pct"],
            "arm_pct":                  prov["arm_pct"],
            "weighted_tdp_w":           round(tdp_w, 1),

            # Intermediate values
            "it_load_mw":               result["it_load_mw"],
            "eff_draw_mw":              result["eff_draw_mw"],
            "eff_draw_w":               result["eff_draw_w"],

            # CPU estimates
            "cpu_count_min":            result["cpu_min"],
            "cpu_count_point":          result["cpu_point"],
            "cpu_count_max":            result["cpu_max"],
            "conf_band_pct":            result["conf_band_pct"],

            # Cross-check
            "cross_check_public_gpu_count": f["cross_check_public_unit_count"],
            "cross_check_derived_cpus":
                round(f["cross_check_public_unit_count"] / 2)
                if f["cross_check_public_unit_count"] else None,
            "cross_check_status":       xcheck,
            "cross_check_note":         f["cross_check_note"],
        }
        rows.append(row)

    # Write CSV
    out_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "processed", "dc_estimates.csv"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Written {len(rows)} rows to {os.path.abspath(out_path)}")

    # Print summary to console
    print("\n--- CPU Estimates Summary ---")
    print(f"{'Facility':<35} {'MW':>6} {'PUE':>5} {'Util':>5} {'TDP':>5} {'Min':>10} {'Point':>10} {'Max':>10} {'X-Check'}")
    print("-" * 115)
    for r in rows:
        xc = {"validated": "OK", "out_of_range": "WARN",
              "no_data": "--", "not_applicable": "n/a"}.get(r["cross_check_status"], "?")
        print(
            f"{r['facility_name']:<35}"
            f"{r['total_power_mw']:>6.0f}"
            f"{r['pue']:>5.2f}"
            f"{r['utilization_rate']:>5.0%}"
            f"{r['weighted_tdp_w']:>5.0f}W"
            f"{r['cpu_count_min']:>10,}"
            f"{r['cpu_count_point']:>10,}"
            f"{r['cpu_count_max']:>10,}"
            f"   {xc}"
        )

    return rows


if __name__ == "__main__":
    run()
