CREATE TABLE IF NOT EXISTS companies (
    company_id      VARCHAR(20)  PRIMARY KEY,
    company_name    VARCHAR(100) NOT NULL,
    industry        VARCHAR(50)  NOT NULL,
    city            VARCHAR(80),
    employee_count  INT,
    risk_profile    DECIMAL(4,3),
    base_premium    BIGINT,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id  VARCHAR(16)  PRIMARY KEY,
    company_id   VARCHAR(20)  NOT NULL REFERENCES companies(company_id),
    age          SMALLINT,
    gender       CHAR(1),
    bmi          DECIMAL(4,1),
    smoker       SMALLINT     DEFAULT 0,
    diabetic     SMALLINT     DEFAULT 0,
    hypertension SMALLINT     DEFAULT 0,
    job_category VARCHAR(20),
    created_at   TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employees_company ON employees(company_id);

CREATE TABLE IF NOT EXISTS telemetry (
    id               BIGSERIAL   PRIMARY KEY,
    employee_id      VARCHAR(16) NOT NULL REFERENCES employees(employee_id),
    company_id       VARCHAR(20) NOT NULL,
    month            SMALLINT,
    avg_daily_steps  INT,
    resting_hr       SMALLINT,
    active_minutes   SMALLINT,
    sleep_hours      DECIMAL(3,1),
    spo2             DECIMAL(4,1),
    recorded_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_employee ON telemetry(employee_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_company  ON telemetry(company_id);

CREATE TABLE IF NOT EXISTS clinical_events (
    event_id      VARCHAR(20)  PRIMARY KEY,
    employee_id   VARCHAR(16)  NOT NULL REFERENCES employees(employee_id),
    company_id    VARCHAR(20)  NOT NULL,
    month         SMALLINT,
    event_type    VARCHAR(30),
    icd10_code    VARCHAR(10),
    claim_amount  DECIMAL(12,2),
    hospitalized  SMALLINT     DEFAULT 0,
    recorded_at   TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clinical_employee ON clinical_events(employee_id);
CREATE INDEX IF NOT EXISTS idx_clinical_company  ON clinical_events(company_id);

CREATE TABLE IF NOT EXISTS training_snapshots (
    snapshot_id         BIGSERIAL   PRIMARY KEY,
    employee_id         VARCHAR(16),
    company_id          VARCHAR(20),
    age                 SMALLINT,
    gender              CHAR(1),
    bmi                 DECIMAL(4,1),
    smoker              SMALLINT,
    diabetic            SMALLINT,
    hypertension        SMALLINT,
    job_category        VARCHAR(20),
    avg_daily_steps     DECIMAL(10,2),
    step_volatility     DECIMAL(10,2),
    avg_resting_hr      DECIMAL(5,1),
    hr_trend            DECIMAL(10,4),
    avg_active_mins     DECIMAL(5,1),
    avg_sleep_hours     DECIMAL(4,1),
    avg_spo2            DECIMAL(4,1),
    total_claims        DECIMAL(12,2),
    visit_count         DECIMAL(8,1),
    hospitalized_count  DECIMAL(8,1),
    premium_share       DECIMAL(12,2),
    loss_ratio          DECIMAL(8,4),
    high_risk           SMALLINT,
    chronic_count       SMALLINT,
    computed_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_company ON training_snapshots(company_id);