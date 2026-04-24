-- =============================================================================
-- Dark Capacity: DC CPU Estimation Model
-- Schema: PostgreSQL
-- Author: Gargee Nimdeo
-- =============================================================================

-- Drop in reverse dependency order for clean re-runs
DROP TABLE IF EXISTS estimates;
DROP TABLE IF EXISTS facilities;
DROP TABLE IF EXISTS provider_assumptions;


-- =============================================================================
-- TABLE 1: provider_assumptions
-- One row per provider. Source of PUE, utilization, and CPU mix defaults.
-- =============================================================================
CREATE TABLE provider_assumptions (
    provider_key        VARCHAR(20)  PRIMARY KEY,
    provider_name       VARCHAR(60)  NOT NULL,
    provider_type       VARCHAR(20)  NOT NULL,  -- 'CPU-Mix', 'GPU-Centric', 'CPU-Heavy'
    pue                 NUMERIC(4,2) NOT NULL,
    pue_source          TEXT         NOT NULL,
    utilization_rate    NUMERIC(4,2) NOT NULL,  -- decimal, e.g. 0.85
    util_source         TEXT         NOT NULL,
    intel_pct           SMALLINT     NOT NULL,  -- % of CPU sockets running Intel Xeon
    amd_pct             SMALLINT     NOT NULL,  -- % of CPU sockets running AMD EPYC
    arm_pct             SMALLINT     NOT NULL,  -- % of CPU sockets running ARM/custom
    weighted_tdp_w      NUMERIC(6,1) NOT NULL,  -- blended TDP in watts
    CONSTRAINT cpu_mix_sums_to_100 CHECK (intel_pct + amd_pct + arm_pct = 100)
);

INSERT INTO provider_assumptions VALUES
    ('google',    'Google',            'CPU-Mix',    1.09, 'Google 2024 Environmental Report',                        0.85, 'LBNL 2024 US Data Center Energy Report', 25, 15, 60, 168.0),
    ('aws',       'AWS',               'CPU-Mix',    1.15, 'AWS Sustainability Report 2024',                          0.85, 'LBNL 2024 US Data Center Energy Report', 30, 15, 55, 178.5),
    ('meta',      'Meta',              'CPU-Mix',    1.08, 'Meta 2024 Environmental Data Report',                     0.85, 'LBNL 2024 US Data Center Energy Report', 40, 35, 25, 251.0),
    ('azure',     'Microsoft Azure',   'CPU-Mix',    1.16, 'Microsoft CSR 2024',                                      0.85, 'LBNL 2024 US Data Center Energy Report', 35, 30, 35, 227.3),
    ('coreweave', 'CoreWeave',         'GPU-Centric',1.35, 'Not disclosed, modeled as mid-tier colo',                 0.77, 'Uptime Institute 2024, neocloud estimate',50, 40, 10, 285.5),
    ('nebius',    'Nebius',            'GPU-Centric',1.10, 'Nebius SEC 6-K FY2024, Finland Mantsala site',            0.77, 'Uptime Institute 2024, neocloud estimate',50, 40, 10, 285.5),
    ('scaleway',  'Scaleway',          'CPU-Mix',    1.30, 'Scaleway Environmental Leadership 2024',                  0.68, 'Uptime Institute 2024, Tier 2 estimate',  55, 35, 10, 283.5);


-- =============================================================================
-- TABLE 2: facilities
-- One row per data center facility. Sourced power figures only.
-- =============================================================================
CREATE TABLE facilities (
    facility_id                     VARCHAR(40)  PRIMARY KEY,
    facility_name                   VARCHAR(100) NOT NULL,
    provider_key                    VARCHAR(20)  NOT NULL REFERENCES provider_assumptions(provider_key),
    location                        VARCHAR(100) NOT NULL,
    year_online                     SMALLINT,
    total_power_mw                  NUMERIC(8,1) NOT NULL,
    power_source                    TEXT         NOT NULL,
    cross_check_public_gpu_count    INTEGER,
    cross_check_note                TEXT
);

INSERT INTO facilities VALUES
    ('google_council_bluffs', 'Google Council Bluffs IA',          'google',    'Council Bluffs, Iowa, USA',         2012, 602.0,  'Baxtel tracker: 8 sites, 602 MW campus total',                                                   NULL,  NULL),
    ('google_the_dalles',     'Google The Dalles OR',               'google',    'The Dalles, Oregon, USA',           2006,  80.0,  'Baxtel Oregon market: Google Dalles 5 at 80 MW',                                                 NULL,  NULL),
    ('google_ashburn',        'Google Ashburn VA',                  'google',    'Ashburn, Virginia, USA',            2018, 100.0,  'Interconnection.fyi public permit record: 100 MW',                                               NULL,  NULL),
    ('aws_ashburn',           'AWS Ashburn VA',                     'aws',       'Ashburn, Virginia, USA',            2016, 202.7,  'Datacenter.fyi: 202.7 MW, Amazon Data Services permit, Dominion Energy grid',                    NULL,  NULL),
    ('aws_hilliard',          'AWS Hilliard OH Cosgray Campus',     'aws',       'Hilliard, Ohio, USA',               2015,  60.0,  'Baxtel: Cosgray Campus 60 MW. AEP fuel cell permit for 73 MW confirms scale.',                   NULL,  NULL),
    ('meta_dekalb',           'Meta DeKalb IL',                     'meta',      'DeKalb, Illinois, USA',             2023,  40.0,  'Interconnection.fyi: 25-50 MW range, midpoint 40 MW. $1B campus investment.',                    NULL,  NULL),
    ('meta_prineville',       'Meta Prineville OR Campus',          'meta',      'Prineville, Oregon, USA',           2011, 112.0,  'DCD sustainability: 982,177 MWh annual usage implies ~112 MW avg draw',                          NULL,  NULL),
    ('meta_altoona',          'Meta Altoona IA',                    'meta',      'Altoona, Iowa, USA',                2015, 142.0,  'DCD sustainability: 1,243,306 MWh annual usage implies ~142 MW avg draw',                        NULL,  NULL),
    ('msft_boydton',          'Microsoft Boydton VA',               'azure',     'Boydton, Virginia, USA',            2024, 412.5,  'Datacenter.fyi public permit: 412.5 MW, operational April 2024, Dominion Energy VA',             NULL,  NULL),
    ('msft_quincy',           'Microsoft Quincy WA Campus',         'azure',     'Quincy, Washington, USA',           2007, 150.0,  'Campus estimate: 800,000 sqft, historical permits confirm ~150 MW range',                        NULL,  NULL),
    ('coreweave_plano',       'CoreWeave Plano TX',                 'coreweave', 'Plano, Texas, USA',                 2024, 120.0,  'CoreWeave/Nvidia press: $1.6B, 3,500+ H100s. IT load est. 120 MW.',                             3500, '3,500 H100 GPUs disclosed. 1 CPU per 2 GPUs implies ~1,750 host CPUs.'),
    ('coreweave_lancaster',   'CoreWeave Lancaster PA',             'coreweave', 'Lancaster, Pennsylvania, USA',      2025, 100.0,  'CoreWeave press July 2025: 100 MW initial, expandable to 300 MW',                                NULL,  NULL),
    ('nebius_mantsala',       'Nebius Mantsala Finland',            'nebius',    'Mantsala, Finland',                 2024,  75.0,  'Nebius press October 2024: tripled capacity to 75 MW, up to 60,000 GPUs',                        60000, '60,000 GPUs disclosed. 1 CPU per 2 GPUs implies ~30,000 host CPUs.'),
    ('nebius_kc',             'Nebius Kansas City MO',              'nebius',    'Kansas City, Missouri, USA',        2025,  35.0,  'Nebius 2025 US expansion: first US cluster, up to 35,000 GPUs, est. 35 MW initial',              35000, '35,000 GPUs planned. 1 CPU per 2 GPUs implies ~17,500 host CPUs.'),
    ('scaleway_par5',         'Scaleway PAR-DC5 Paris',             'scaleway',  'Paris, France',                     2024,  30.0,  'Scaleway Environmental 2024: AI cluster, PUE 1.25. Capacity est. 30 MW.',                        NULL,  NULL);


-- =============================================================================
-- TABLE 3: estimates
-- One row per facility. All formula outputs. Populated by Python model.
-- =============================================================================
CREATE TABLE estimates (
    facility_id         VARCHAR(40)   PRIMARY KEY REFERENCES facilities(facility_id),
    it_load_mw          NUMERIC(10,2) NOT NULL,
    eff_draw_mw         NUMERIC(10,2) NOT NULL,
    eff_draw_w          BIGINT        NOT NULL,
    cpu_count_min       INTEGER       NOT NULL,
    cpu_count_point     INTEGER       NOT NULL,
    cpu_count_max       INTEGER       NOT NULL,
    conf_band_pct       NUMERIC(6,1)  NOT NULL,
    cross_check_derived_cpus INTEGER,
    cross_check_status  VARCHAR(20),  -- 'validated', 'out_of_range', 'no_data', 'not_applicable'
    estimated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate from Python CSV output (run after Python script):
-- \COPY estimates FROM 'data/processed/dc_estimates.csv' CSV HEADER;
-- Or insert manually using values from the CSV.
