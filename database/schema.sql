-- ============================================================
-- Student Leave Management System
-- Database Schema
-- PostgreSQL 14+
-- ============================================================

-- CLEANUP (safe to re-run)
DROP VIEW  IF EXISTS v_leave_details CASCADE;
DROP VIEW  IF EXISTS v_pending_leaves CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS leave_applications CASCADE;
DROP TABLE IF EXISTS leave_types CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP FUNCTION IF EXISTS update_reviewed_at() CASCADE;
DROP FUNCTION IF EXISTS log_status_change() CASCADE;

-- ============================================================
-- TABLE 1: users
-- ============================================================
CREATE TABLE users (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    email           VARCHAR(100)    UNIQUE NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL
                    CHECK (role IN ('student', 'faculty', 'admin')),
    year            VARCHAR(20)
                    CHECK (
                        year IS NULL
                        OR year IN ('1st Year', '2nd Year', '3rd Year', '4th Year', 'Final Year')
                    ),
    department      VARCHAR(100),
    phone           VARCHAR(20),
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT year_only_for_students CHECK (
        (role = 'student' AND year IS NOT NULL)
        OR
        (role IN ('faculty', 'admin') AND year IS NULL)
    )
);

COMMENT ON TABLE  users               IS 'All system users: students, faculty, admins';
COMMENT ON COLUMN users.role          IS 'Access role: student | faculty | admin';
COMMENT ON COLUMN users.year          IS 'Year of study (students only, NULL for others)';
COMMENT ON COLUMN users.password_hash IS 'PBKDF2-SHA256 hash, never plain text';

-- ============================================================
-- TABLE 2: leave_types
-- ============================================================
CREATE TABLE leave_types (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(50)     UNIQUE NOT NULL,
    description     TEXT,
    max_days        INTEGER         DEFAULT 30,
    requires_doc    BOOLEAN         DEFAULT FALSE,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  leave_types              IS 'Configurable leave categories';
COMMENT ON COLUMN leave_types.requires_doc IS 'TRUE if medical certificate required';

-- ============================================================
-- TABLE 3: leave_applications
-- ============================================================
CREATE TABLE leave_applications (
    id              SERIAL          PRIMARY KEY,
    student_id      INTEGER         NOT NULL
                    REFERENCES users(id) ON DELETE CASCADE,
    leave_type_id   INTEGER         NOT NULL
                    REFERENCES leave_types(id) ON DELETE RESTRICT,
    reason          TEXT            NOT NULL,
    start_date      DATE            NOT NULL,
    end_date        DATE            NOT NULL,
    total_days      INTEGER         GENERATED ALWAYS AS
                    ((end_date - start_date) + 1) STORED,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    reviewed_by     INTEGER
                    REFERENCES users(id) ON DELETE SET NULL,
    reviewer_comment TEXT,
    document_url    VARCHAR(255),
    submitted_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    reviewed_at     TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_date_range CHECK (end_date >= start_date),
    CONSTRAINT reason_not_empty CHECK (LENGTH(TRIM(reason)) > 0)
);

COMMENT ON TABLE  leave_applications              IS 'Leave requests from students';
COMMENT ON COLUMN leave_applications.status       IS 'pending | approved | rejected | cancelled';
COMMENT ON COLUMN leave_applications.total_days   IS 'Auto-computed inclusive day count';
COMMENT ON COLUMN leave_applications.document_url IS 'Optional supporting document link';

-- ============================================================
-- TABLE 4: notifications
-- ============================================================
CREATE TABLE notifications (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL
                    REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(100)    NOT NULL,
    message         TEXT            NOT NULL,
    type            VARCHAR(30)     DEFAULT 'info'
                    CHECK (type IN ('info', 'success', 'warning', 'error')),
    related_leave_id INTEGER
                    REFERENCES leave_applications(id) ON DELETE SET NULL,
    is_read         BOOLEAN         DEFAULT FALSE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE notifications IS 'In-app notifications for users';

-- ============================================================
-- TABLE 5: audit_log
-- ============================================================
CREATE TABLE audit_log (
    id              SERIAL          PRIMARY KEY,
    user_id         INTEGER
                    REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(50)     NOT NULL,
    entity_type     VARCHAR(50),
    entity_id       INTEGER,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      VARCHAR(45),
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE audit_log IS 'Security audit trail of important actions';

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_users_email         ON users(email);
CREATE INDEX idx_users_role          ON users(role);
CREATE INDEX idx_users_year          ON users(year);
CREATE INDEX idx_users_role_year     ON users(role, year);
CREATE INDEX idx_users_active        ON users(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_leaves_student      ON leave_applications(student_id);
CREATE INDEX idx_leaves_reviewer     ON leave_applications(reviewed_by);
CREATE INDEX idx_leaves_status       ON leave_applications(status);
CREATE INDEX idx_leaves_type         ON leave_applications(leave_type_id);
CREATE INDEX idx_leaves_dates        ON leave_applications(start_date, end_date);
CREATE INDEX idx_leaves_student_status ON leave_applications(student_id, status);
CREATE INDEX idx_leaves_pending      ON leave_applications(submitted_at)
                                     WHERE status = 'pending';

CREATE INDEX idx_notif_user          ON notifications(user_id);
CREATE INDEX idx_notif_unread        ON notifications(user_id, is_read)
                                     WHERE is_read = FALSE;

CREATE INDEX idx_audit_user          ON audit_log(user_id);
CREATE INDEX idx_audit_created       ON audit_log(created_at DESC);

-- ============================================================
-- TRIGGERS
-- ============================================================
CREATE OR REPLACE FUNCTION update_reviewed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('approved', 'rejected') AND OLD.status = 'pending' THEN
        NEW.reviewed_at := CURRENT_TIMESTAMP;
    END IF;
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_leaves_reviewed_at
BEFORE UPDATE ON leave_applications
FOR EACH ROW EXECUTE FUNCTION update_reviewed_at();

CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_value, new_value)
        VALUES (
            NEW.reviewed_by,
            'STATUS_CHANGE',
            'leave_application',
            NEW.id,
            jsonb_build_object('status', OLD.status),
            jsonb_build_object('status', NEW.status)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_leaves_audit
AFTER UPDATE ON leave_applications
FOR EACH ROW EXECUTE FUNCTION log_status_change();

-- ============================================================
-- VIEWS
-- ============================================================
CREATE VIEW v_pending_leaves AS
SELECT
    la.id,
    la.student_id,
    u.name          AS student_name,
    u.email         AS student_email,
    u.year          AS student_year,
    u.department    AS student_department,
    lt.name         AS leave_type,
    la.reason,
    la.start_date,
    la.end_date,
    la.total_days,
    la.submitted_at
FROM leave_applications la
JOIN users u        ON u.id = la.student_id
JOIN leave_types lt ON lt.id = la.leave_type_id
WHERE la.status = 'pending'
ORDER BY la.submitted_at ASC;

CREATE VIEW v_leave_details AS
SELECT
    la.id,
    la.student_id,
    s.name          AS student_name,
    s.email         AS student_email,
    s.year          AS student_year,
    s.department    AS student_department,
    lt.name         AS leave_type,
    la.reason,
    la.start_date,
    la.end_date,
    la.total_days,
    la.status,
    la.reviewed_by,
    f.name          AS reviewer_name,
    la.reviewer_comment,
    la.submitted_at,
    la.reviewed_at
FROM leave_applications la
JOIN users s        ON s.id = la.student_id
JOIN leave_types lt ON lt.id = la.leave_type_id
LEFT JOIN users f   ON f.id = la.reviewed_by;

-- ============================================================
-- INITIAL DATA — leave types
-- ============================================================
INSERT INTO leave_types (name, description, max_days, requires_doc) VALUES
    ('Medical',  'Medical appointments, illness, recovery', 30, TRUE),
    ('Personal', 'Personal matters',                        10, FALSE),
    ('Family',   'Family emergencies or events',            15, FALSE),
    ('Academic', 'Conferences, competitions, research',     10, TRUE),
    ('Other',    'Other reasons, subject to approval',       7, FALSE);

-- ============================================================
-- END OF SCHEMA
-- ============================================================
