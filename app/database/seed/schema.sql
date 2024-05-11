CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE org_customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    org_code VARCHAR(255) UNIQUE NOT NULL,
    stripe_id VARCHAR(255),
    sub_start INT,
    sub_end INT,
    slps TEXT[]
);


CREATE TABLE slps (
    slp_id VARCHAR(255) PRIMARY KEY,
    account_creation_epoch BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    free_trial_exp BIGINT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP + INTERVAL '14 days'),
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    sub_type INT DEFAULT 0,
    stripe_id VARCHAR(255),
    sub_start INT,
    sub_end INT,
    org_id INT
);

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    slp_id VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    age INT,
    FOREIGN KEY (slp_id) REFERENCES slps(slp_id)
);

CREATE TABLE lsas (
    lsa_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    name VARCHAR(255),
    timestamp DATE NOT NULL,
    audiofile_url TEXT,
    audio_type TEXT DEFAULT NULL,
    transcription TEXT,
    transcription_automated BOOLEAN,
    transcription_final BOOLEAN,
    mlu_sugar_morph_count INTEGER,
    mlu DECIMAL(10, 2),
    tnw INT,
    wps DECIMAL(10, 2),
    cps DECIMAL(10, 2),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);


CREATE TYPE sentence_status AS ENUM ('true', 'false', 'unsure');
CREATE TABLE utterances (
  utterance_id SERIAL PRIMARY KEY,
  lsa_id INT NOT NULL,
  utterance_text TEXT,
  utterance_order INT,
  start_text INT,
  end_text INT,
  morph_sugar_count INT DEFAULT 0,
  utterance_sugar_obj JSONB,
  sentence sentence_status DEFAULT 'false',
  clause_count INTEGER DEFAULT 0,
  FOREIGN KEY (lsa_id) REFERENCES lsas(lsa_id) ON DELETE CASCADE
);
