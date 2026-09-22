PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('coordinator','technician')),
    skills TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY,
    reference TEXT NOT NULL UNIQUE,
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    equipment TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('lighting','sewing','appliances','audio')),
    description TEXT NOT NULL,
    priority TEXT NOT NULL CHECK(priority IN ('normal','high')),
    status TEXT NOT NULL CHECK(status IN ('new','assessing','queued','repairing','ready','closed','cancelled')),
    assigned_to TEXT REFERENCES users(id),
    estimated_minutes INTEGER CHECK(estimated_minutes IS NULL OR estimated_minutes > 0),
    quote_cents INTEGER CHECK(quote_cents IS NULL OR quote_cents >= 0),
    approval_status TEXT NOT NULL DEFAULT 'not_requested' CHECK(approval_status IN ('not_requested','pending','approved','declined')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    status TEXT NOT NULL CHECK(status IN ('needed','ordered','received')),
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    actor TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    body TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('queued','accepted','failed')),
    attempts INTEGER NOT NULL DEFAULT 0,
    provider_reference TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS imported_events (
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    event_id TEXT NOT NULL,
    request_id INTEGER NOT NULL REFERENCES requests(id),
    PRIMARY KEY (organization_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_requests_org ON requests(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_activity_request ON activity(request_id, id);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
