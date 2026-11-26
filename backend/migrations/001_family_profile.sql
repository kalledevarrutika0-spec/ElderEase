-- Supabase/PostgreSQL migration for family profile MVP
-- Run in the Supabase SQL Editor. It is safe to run more than once.

ALTER TABLE caregivers ADD COLUMN IF NOT EXISTS auth_user_id VARCHAR(255);
ALTER TABLE caregivers ADD COLUMN IF NOT EXISTS family_id INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS uq_caregivers_auth_user_id
  ON caregivers(auth_user_id);
CREATE INDEX IF NOT EXISTS ix_caregivers_family_id ON caregivers(family_id);

ALTER TABLE medicines ADD COLUMN IF NOT EXISTS family_id INTEGER;
CREATE INDEX IF NOT EXISTS ix_medicines_family_id ON medicines(family_id);

ALTER TABLE appointments ADD COLUMN IF NOT EXISTS family_id INTEGER;
CREATE INDEX IF NOT EXISTS ix_appointments_family_id ON appointments(family_id);

CREATE TABLE IF NOT EXISTS family_profiles (
  id SERIAL PRIMARY KEY,
  family_name VARCHAR(120) NOT NULL,
  elder_name VARCHAR(120) NOT NULL,
  elder_age INTEGER,
  elder_care_notes TEXT,
  invite_code VARCHAR(32) NOT NULL UNIQUE,
  primary_caregiver_id INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS family_members (
  id BIGSERIAL PRIMARY KEY,
  family_id INTEGER NOT NULL REFERENCES family_profiles(id) ON DELETE CASCADE,
  caregiver_id INTEGER NOT NULL UNIQUE REFERENCES caregivers(id) ON DELETE CASCADE,
  auth_user_id VARCHAR(255) NOT NULL UNIQUE,
  role VARCHAR(80) NOT NULL,
  relationship VARCHAR(40) NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_family_members_family_id
  ON family_members(family_id);

-- Safely backfill the existing single/demo care workspace.
-- This creates no duplicate care records and assigns existing records once.
INSERT INTO family_profiles (
  family_name,
  elder_name,
  elder_age,
  elder_care_notes,
  invite_code,
  primary_caregiver_id
)
SELECT
  'Demo Care Family',
  'Demo Care Recipient',
  78,
  'Synthetic demo family profile.',
  'DEMOFAMILY12',
  (SELECT id FROM caregivers ORDER BY id LIMIT 1)
WHERE NOT EXISTS (
  SELECT 1 FROM family_profiles
  WHERE invite_code = 'DEMOFAMILY12'
);

WITH demo_family AS (
  SELECT id FROM family_profiles
  WHERE invite_code = 'DEMOFAMILY12'
  ORDER BY id
  LIMIT 1
)
UPDATE caregivers
SET family_id = (SELECT id FROM demo_family)
WHERE family_id IS NULL;

WITH demo_family AS (
  SELECT id FROM family_profiles
  WHERE invite_code = 'DEMOFAMILY12'
  ORDER BY id
  LIMIT 1
)
UPDATE medicines
SET family_id = COALESCE(
  (SELECT c.family_id FROM caregivers c
   WHERE c.id = medicines.assigned_caregiver_id),
  (SELECT id FROM demo_family)
)
WHERE family_id IS NULL;

WITH demo_family AS (
  SELECT id FROM family_profiles
  WHERE invite_code = 'DEMOFAMILY12'
  ORDER BY id
  LIMIT 1
)
UPDATE appointments
SET family_id = COALESCE(
  (SELECT c.family_id FROM caregivers c
   WHERE c.id = appointments.assigned_caregiver_id),
  (SELECT id FROM demo_family)
)
WHERE family_id IS NULL;

-- Stock transactions and dose logs follow their medicine relationship.
-- Notifications follow their recipient caregiver relationship.
-- They intentionally receive no redundant family_id columns.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_caregivers_family'
  ) THEN
    ALTER TABLE caregivers
      ADD CONSTRAINT fk_caregivers_family
      FOREIGN KEY (family_id) REFERENCES family_profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_medicines_family'
  ) THEN
    ALTER TABLE medicines
      ADD CONSTRAINT fk_medicines_family
      FOREIGN KEY (family_id) REFERENCES family_profiles(id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_appointments_family'
  ) THEN
    ALTER TABLE appointments
      ADD CONSTRAINT fk_appointments_family
      FOREIGN KEY (family_id) REFERENCES family_profiles(id) ON DELETE CASCADE;
  END IF;
END $$;
