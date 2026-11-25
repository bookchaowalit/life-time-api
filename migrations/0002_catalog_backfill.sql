-- platform-empire SPEC-002 rollout step 4: classify the time logs written before the producer existed.
-- For every existing time log this queues, in the cell outbox, a lifecycle `.updated` event (time logs never
-- emitted, so this creates the graph node; the payload stays bare like cell.yaml `graph: []`) followed by the
-- `in-domain` set event (`mode: replace`) under the cell.yaml mapping, both at the row's current version. The
-- publisher (time-api inline sweep or the time-publisher cron) delivers them; the graph keeps the highest
-- set_version, so a row that already sent its set event, or that is edited later, turns these into `stale`
-- (rollout AC-23: a second run adds no edges).
--
-- time_logs and outbox FORCE row level security and the migrator binds no workspace, so FORCE is lifted for these
-- statements only (same transaction). ALTER TABLE takes ACCESS EXCLUSIVE on both, so no write can land between
-- reading a row's version and queueing its events. Keep the CASE in step with cell.yaml (tests compare them).
ALTER TABLE time.time_logs NO FORCE ROW LEVEL SECURITY;
ALTER TABLE time.outbox NO FORCE ROW LEVEL SECURITY;

INSERT INTO time.outbox (workspace_id, type, subject, classification, payload, occurred_at)
SELECT l.workspace_id, e.type, 'empire:time:time-log:' || l.id, 'confidential', e.payload,
       now() + e.n * interval '1 microsecond'
FROM time.time_logs l
CROSS JOIN LATERAL (VALUES
    (0, 'time.time-log.updated', jsonb_build_object('version', l.version, 'deleted', false)),
    (1, 'time.time-log.linked', jsonb_build_object(
        'relation', 'in-domain',
        'mode', 'replace',
        'targets', jsonb_build_array('empire:platform:domain:' || CASE l.domain
            WHEN 'work' THEN 'work'
            WHEN 'learning' THEN 'skills'
            ELSE 'unclassified' END),
        'set_version', l.version,
        'version', l.version))
) AS e(n, type, payload)
ORDER BY l.workspace_id, l.id, e.n;

ALTER TABLE time.time_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE time.outbox FORCE ROW LEVEL SECURITY;
