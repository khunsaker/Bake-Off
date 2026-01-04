-- =============================================================================
-- S3: Two-Hop Relationship Query
-- Query: Find all aircraft operated by organizations headquartered in a country
-- Expected p99: 30-50ms (2 JOINs with indexes)
-- =============================================================================

-- Find aircraft by operator's HQ country
SELECT
    a.shark_name AS aircraft_name,
    a.platform AS aircraft_platform,
    o.name AS operator_name,
    l.name AS headquarters_location,
    l.country
FROM air_instance_lookup a
INNER JOIN organizations o ON a.operator = o.name
INNER JOIN locations l ON o.parent_org_id IS NOT NULL  -- Placeholder: need HQ relationship
WHERE l.country = $1;

-- Note: This query reveals a schema limitation
-- PostgreSQL denormalized design doesn't naturally express:
--   Aircraft -> Organization -> HQ Location
--
-- We need to either:
-- 1. Add operator_id foreign key to air_instance_lookup
-- 2. Use kb_relationships table for graph-like traversal
-- 3. Accept string matching on operator name (fragile)

-- Alternative using kb_relationships table:
SELECT
    a.shark_name AS aircraft_name,
    a.platform AS aircraft_platform,
    o.name AS operator_name,
    l.name AS headquarters_location
FROM air_instance_lookup a
INNER JOIN kb_relationships r1 ON r1.source_domain = 'AIR' AND r1.source_id = a.id
INNER JOIN organizations o ON r1.target_domain = 'ORGANIZATION' AND r1.target_id = o.id
INNER JOIN kb_relationships r2 ON r2.source_domain = 'ORGANIZATION' AND r2.source_id = o.id
INNER JOIN locations l ON r2.target_domain = 'LOCATION' AND r2.target_id = l.id
WHERE r1.relationship_type = 'OPERATED_BY'
  AND r2.relationship_type = 'HEADQUARTERED_AT'
  AND l.country = $1;

-- Performance notes:
-- - 4 JOINs in relationship-based approach
-- - Multiple index lookups on composite keys
-- - Expected latency: 50-100ms at scale
-- - Query complexity increases rapidly with more hops
-- - This is where graph databases shine
