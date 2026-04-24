-- =============================================================================
-- Dark Capacity: Analytical Queries
-- These queries power the Tableau dashboard and document the analysis logic.
-- Author: Gargee Nimdeo
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1: Facility CPU ranking by point estimate
-- Used in: bar chart of estimated CPU count per facility
-- -----------------------------------------------------------------------------
SELECT
    f.facility_name,
    f.location,
    pa.provider_name,
    pa.provider_type,
    f.total_power_mw,
    e.cpu_count_min,
    e.cpu_count_point,
    e.cpu_count_max,
    e.conf_band_pct,
    ROUND(e.cpu_count_point::NUMERIC / f.total_power_mw, 0) AS cpu_per_mw,
    e.cross_check_status
FROM estimates e
JOIN facilities f ON e.facility_id = f.facility_id
JOIN provider_assumptions pa ON f.provider_key = pa.provider_key
ORDER BY e.cpu_count_point DESC;


-- -----------------------------------------------------------------------------
-- Q2: CPU density per MW by provider type
-- Answers: which provider type gets the most CPUs out of each MW of power?
-- Used in: comparison table / heatmap in Tableau
-- -----------------------------------------------------------------------------
SELECT
    pa.provider_type,
    pa.provider_name,
    ROUND(AVG(pa.pue), 2)                                           AS avg_pue,
    ROUND(AVG(pa.utilization_rate), 2)                              AS avg_utilization,
    ROUND(AVG(pa.weighted_tdp_w), 1)                                AS avg_weighted_tdp_w,
    ROUND(AVG(e.cpu_count_point::NUMERIC / f.total_power_mw), 0)   AS avg_cpu_per_mw,
    SUM(f.total_power_mw)                                           AS total_mw_in_sample,
    SUM(e.cpu_count_point)                                          AS total_cpu_est
FROM estimates e
JOIN facilities f  ON e.facility_id  = f.facility_id
JOIN provider_assumptions pa ON f.provider_key = pa.provider_key
GROUP BY pa.provider_type, pa.provider_name
ORDER BY avg_cpu_per_mw DESC;


-- -----------------------------------------------------------------------------
-- Q3: PUE sensitivity analysis
-- Shows how CPU count changes as PUE shifts +/- 0.1 from the default
-- Used in: sensitivity chart in Tableau
-- -----------------------------------------------------------------------------
WITH pue_scenarios AS (
    SELECT
        f.facility_id,
        f.facility_name,
        pa.provider_name,
        f.total_power_mw,
        pa.pue                                                      AS pue_actual,
        pa.utilization_rate,
        pa.weighted_tdp_w,

        -- Base estimate
        ROUND((f.total_power_mw / pa.pue) * pa.utilization_rate * 1e6 / pa.weighted_tdp_w)
                                                                    AS cpu_base,

        -- PUE pessimistic (+0.1 = less efficient)
        ROUND((f.total_power_mw / (pa.pue + 0.1)) * pa.utilization_rate * 1e6 / pa.weighted_tdp_w)
                                                                    AS cpu_pue_high,

        -- PUE optimistic (-0.1 = more efficient)
        ROUND((f.total_power_mw / GREATEST(pa.pue - 0.1, 1.05)) * pa.utilization_rate * 1e6 / pa.weighted_tdp_w)
                                                                    AS cpu_pue_low
    FROM facilities f
    JOIN provider_assumptions pa ON f.provider_key = pa.provider_key
)
SELECT
    facility_name,
    provider_name,
    pue_actual,
    cpu_pue_high    AS cpu_if_pue_plus_0_1,
    cpu_base        AS cpu_at_current_pue,
    cpu_pue_low     AS cpu_if_pue_minus_0_1,
    cpu_pue_low - cpu_pue_high  AS cpu_swing_across_0_2_pue_range
FROM pue_scenarios
ORDER BY cpu_swing_across_0_2_pue_range DESC;


-- -----------------------------------------------------------------------------
-- Q4: Utilization sensitivity analysis
-- Shows how CPU count shifts as utilization changes from 60% to 95%
-- Used in: sensitivity surface in Tableau
-- -----------------------------------------------------------------------------
WITH util_levels AS (
    SELECT unnest(ARRAY[0.60, 0.70, 0.77, 0.85, 0.90, 0.95]) AS util_rate
)
SELECT
    f.facility_name,
    pa.provider_name,
    pa.provider_type,
    ul.util_rate,
    ROUND(
        (f.total_power_mw / pa.pue) * ul.util_rate * 1e6 / pa.weighted_tdp_w
    ) AS cpu_at_util_level
FROM facilities f
CROSS JOIN util_levels ul
JOIN provider_assumptions pa ON f.provider_key = pa.provider_key
ORDER BY f.facility_name, ul.util_rate;


-- -----------------------------------------------------------------------------
-- Q5: Cross-check validation summary
-- Summarises where model estimates align with public disclosures
-- Used in: methodology validation section of write-up
-- -----------------------------------------------------------------------------
SELECT
    f.facility_name,
    pa.provider_name,
    pa.provider_type,
    f.cross_check_public_gpu_count,
    ROUND(f.cross_check_public_gpu_count::NUMERIC / 2)             AS derived_host_cpus,
    e.cpu_count_point                                               AS model_cpu_estimate,
    e.cross_check_status,
    ROUND(
        ABS(e.cpu_count_point - (f.cross_check_public_gpu_count / 2.0))
        / NULLIF((f.cross_check_public_gpu_count / 2.0), 0) * 100, 1
    )                                                               AS pct_diff_from_expected,
    f.cross_check_note
FROM facilities f
JOIN estimates e ON f.facility_id = e.facility_id
JOIN provider_assumptions pa ON f.provider_key = pa.provider_key
WHERE f.cross_check_public_gpu_count IS NOT NULL
ORDER BY pct_diff_from_expected ASC;


-- -----------------------------------------------------------------------------
-- Q6: Full joined view for Tableau data source (single flat table)
-- Connect Tableau directly to this view or export as CSV
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_tableau_main AS
SELECT
    f.facility_id,
    f.facility_name,
    pa.provider_name,
    pa.provider_type,
    f.location,
    SPLIT_PART(f.location, ',', 2)                                  AS state_or_country,
    SPLIT_PART(f.location, ',', 3)                                  AS region,
    f.year_online,
    f.total_power_mw,
    pa.pue,
    pa.utilization_rate,
    pa.intel_pct,
    pa.amd_pct,
    pa.arm_pct,
    pa.weighted_tdp_w,
    e.it_load_mw,
    e.eff_draw_mw,
    e.cpu_count_min,
    e.cpu_count_point,
    e.cpu_count_max,
    e.conf_band_pct,
    ROUND(e.cpu_count_point::NUMERIC / f.total_power_mw, 0)         AS cpu_per_mw,
    f.cross_check_public_gpu_count,
    e.cross_check_derived_cpus,
    e.cross_check_status,
    f.power_source,
    pa.pue_source
FROM facilities f
JOIN provider_assumptions pa ON f.provider_key  = pa.provider_key
JOIN estimates e              ON f.facility_id   = e.facility_id;
