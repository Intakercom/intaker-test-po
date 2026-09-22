"""Business rules and queries. HTTP and UI concerns live elsewhere."""
import json
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from .database import connect

STATUSES = ['new', 'assessing', 'queued', 'repairing', 'ready', 'closed', 'cancelled']
CATEGORIES = ['lighting', 'sewing', 'appliances', 'audio']
ACTIVE = ['new', 'assessing', 'queued', 'repairing', 'ready']


class APIError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def text_field(data, key, maximum=500, required=True):
    value = data.get(key)
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > maximum:
        raise APIError(400, f'{key} must be text between {1 if required else 0} and {maximum} characters.')
    return value.strip()


def integer(value, name, minimum=1, maximum=10000, nullable=False):
    if nullable and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise APIError(400, f'{name} must be an integer from {minimum} to {maximum}.')
    return value


class Workshop:
    def __init__(self, database_path):
        self.database_path = database_path

    @contextmanager
    def db(self, write=False):
        db = connect(self.database_path)
        try:
            if write:
                db.execute('BEGIN IMMEDIATE')
            yield db
            if write:
                db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def user(self, user_id):
        with self.db() as db:
            row = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            if not row:
                raise APIError(401, 'Choose a valid demo profile.')
            return dict(row)

    def coordinator(self, user):
        if user['role'] != 'coordinator':
            raise APIError(403, 'Only coordinators can perform this action.')

    def scope(self, user, alias='r'):
        sql, args = f'{alias}.organization_id=?', [user['organization_id']]
        if user['role'] == 'technician':
            sql += f' AND {alias}.assigned_to=?'
            args.append(user['id'])
        return sql, args

    def visible(self, db, user, request_id):
        clause, args = self.scope(user)
        row = db.execute(f'SELECT r.* FROM requests r WHERE r.id=? AND {clause}', [request_id, *args]).fetchone()
        if not row:
            raise APIError(404, 'Request not found for this demo profile.')
        return dict(row)

    def version(self, row, data):
        value = data.get('version')
        if isinstance(value, bool) or not isinstance(value, int) or value != row['version']:
            raise APIError(409, 'This request has changed. Refresh it and try again; your changes were not saved.')

    def log(self, db, request_id, actor, event_type, message):
        db.execute('INSERT INTO activity (request_id,actor,event_type,message,created_at) VALUES (?,?,?,?,?)',
                   (request_id, actor, event_type, message, now()))

    def touch(self, db, request_id):
        db.execute('UPDATE requests SET updated_at=?,version=version+1 WHERE id=?', (now(), request_id))

    def bootstrap(self, user):
        with self.db() as db:
            profiles = [dict(row) for row in db.execute('''SELECT u.id,u.name,u.role,o.name organization_name
                FROM users u JOIN organizations o ON o.id=u.organization_id ORDER BY o.name,u.role,u.name''')]
            staff = [dict(row) for row in db.execute('SELECT * FROM users WHERE organization_id=? ORDER BY name', (user['organization_id'],))]
            for person in staff:
                person['skills'] = json.loads(person['skills'])
            org = dict(db.execute('SELECT * FROM organizations WHERE id=?', (user['organization_id'],)).fetchone())
        return {'user': user, 'organization': org, 'profiles': profiles, 'staff': staff, 'statuses': STATUSES, 'categories': CATEGORIES}

    def list_requests(self, user):
        clause, args = self.scope(user)
        with self.db() as db:
            return [dict(row) for row in db.execute(f'''SELECT r.*,u.name owner_name,
                (SELECT COUNT(*) FROM parts p WHERE p.request_id=r.id AND p.status!='received') pending_parts,
                (SELECT COUNT(*) FROM parts p WHERE p.request_id=r.id) part_count
                FROM requests r LEFT JOIN users u ON u.id=r.assigned_to
                WHERE {clause} ORDER BY r.updated_at DESC,r.id DESC''', args)]

    def detail(self, user, request_id):
        with self.db() as db:
            row = self.visible(db, user, request_id)
            for key, table in [('parts', 'parts'), ('activity', 'activity'), ('messages', 'messages')]:
                row[key] = [dict(r) for r in db.execute(f'SELECT * FROM {table} WHERE request_id=? ORDER BY id DESC', (request_id,))]
            return row

    def dashboard(self, user):
        rows = self.list_requests(user)
        active = [r for r in rows if r['status'] in ACTIVE]
        return {
            'active': len(active),
            'new': sum(r['status'] == 'new' for r in active),
            'approval_pending': sum(r['approval_status'] == 'pending' for r in active),
            'waiting_parts': sum(r['pending_parts'] > 0 for r in active),
            'unassigned': sum(r['assigned_to'] is None for r in active),
            'by_status': {s: sum(r['status'] == s for r in rows) for s in STATUSES},
            'by_category': {c: sum(r['category'] == c for r in active) for c in CATEGORIES},
        }

    def create(self, user, data, event_id=None):
        self.coordinator(user)
        if event_id is not None and (not isinstance(event_id, str) or not 1 <= len(event_id.strip()) <= 100):
            raise APIError(400, 'event_id must be non-empty text of at most 100 characters.')
        with self.db(write=True) as db:
            if event_id:
                old = db.execute('SELECT request_id FROM imported_events WHERE organization_id=? AND event_id=?', (user['organization_id'], event_id)).fetchone()
                if old:
                    return {'id': old['request_id'], 'duplicate': True}
            customer = text_field(data, 'customer_name', 100)
            email = text_field(data, 'customer_email', 200)
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                raise APIError(400, 'Enter a valid customer email address.')
            equipment = text_field(data, 'equipment', 120)
            description = text_field(data, 'description', 2000)
            category, priority = data.get('category'), data.get('priority', 'normal')
            if category not in CATEGORIES or priority not in ['normal', 'high']:
                raise APIError(400, 'Choose a valid category and priority.')
            next_id = db.execute('SELECT COALESCE(MAX(id),2000)+1 FROM requests').fetchone()[0]
            prefix = 'BS' if user['organization_id'] == 'benchside' else 'NS'
            timestamp = now()
            db.execute('''INSERT INTO requests
                (id,reference,organization_id,customer_name,customer_email,equipment,category,description,priority,status,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,'new',?,?)''',
                (next_id, f'{prefix}-{next_id}', user['organization_id'], customer, email, equipment, category, description, priority, timestamp, timestamp))
            self.log(db, next_id, user['name'], 'created', 'Request imported from a drop-off form.' if event_id else 'Repair request created at the front desk.')
            if event_id:
                db.execute('INSERT INTO imported_events VALUES (?,?,?)', (user['organization_id'], event_id, next_id))
            return {'id': next_id, 'duplicate': False}

    def update(self, user, request_id, data):
        allowed = {'version', 'status', 'assigned_to', 'priority', 'estimated_minutes'}
        if set(data) - allowed or not (set(data) - {'version'}):
            raise APIError(400, 'Provide supported workflow fields to update.')
        with self.db(write=True) as db:
            row = self.visible(db, user, request_id)
            self.version(row, data)
            updates = {}
            if 'status' in data:
                if data['status'] not in STATUSES:
                    raise APIError(400, 'Choose a valid repair status.')
                # Status is manually managed. Approval and parts are independent records.
                updates['status'] = data['status']
            if 'priority' in data:
                self.coordinator(user)
                if data['priority'] not in ['normal', 'high']:
                    raise APIError(400, 'Choose a valid priority.')
                updates['priority'] = data['priority']
            if 'assigned_to' in data:
                self.coordinator(user)
                target = data['assigned_to']
                if target is not None:
                    owner = db.execute("SELECT id FROM users WHERE id=? AND organization_id=? AND role='technician'", (target, user['organization_id'])).fetchone()
                    if not owner:
                        raise APIError(400, 'Choose a technician in this organization.')
                updates['assigned_to'] = target
            if 'estimated_minutes' in data:
                updates['estimated_minutes'] = integer(data['estimated_minutes'], 'estimated_minutes', maximum=480, nullable=True)
            changed = {k: v for k, v in updates.items() if row[k] != v}
            if changed:
                db.execute('UPDATE requests SET '+','.join(f'{k}=?' for k in changed)+' WHERE id=?', [*changed.values(), request_id])
                for key, value in changed.items():
                    display = value
                    if key == 'assigned_to' and value:
                        display = db.execute('SELECT name FROM users WHERE id=?', (value,)).fetchone()['name']
                    self.log(db, request_id, user['name'], key, f'{key.replace("_", " ").capitalize()} changed to {display if display is not None else "not set"}.')
                self.touch(db, request_id)
        return {'ok': True}

    def action(self, user, request_id, action, data):
        with self.db(write=True) as db:
            row = self.visible(db, user, request_id)
            self.version(row, data)
            if action == 'notes':
                self.log(db, request_id, user['name'], 'note', text_field(data, 'body', 2000))
            elif action == 'parts':
                name = text_field(data, 'name', 120)
                quantity = integer(data.get('quantity', 1), 'quantity', maximum=99)
                db.execute("INSERT INTO parts (request_id,name,quantity,status,updated_at) VALUES (?,?,?,'needed',?)", (request_id, name, quantity, now()))
                self.log(db, request_id, user['name'], 'part', f'Added part: {name} (×{quantity}).')
            elif action == 'part-status':
                part_id = integer(data.get('part_id'), 'part_id', maximum=100000000)
                if data.get('status') not in ['needed', 'ordered', 'received']:
                    raise APIError(400, 'Choose a valid part status.')
                part = db.execute('SELECT * FROM parts WHERE id=? AND request_id=?', (part_id, request_id)).fetchone()
                if not part:
                    raise APIError(404, 'Part not found on this request.')
                db.execute('UPDATE parts SET status=?,updated_at=? WHERE id=?', (data['status'], now(), part_id))
                self.log(db, request_id, user['name'], 'part', f'{part["name"]}: {data["status"]}.')
            elif action == 'quote':
                self.coordinator(user)
                cents = integer(data.get('quote_cents'), 'quote_cents', minimum=0, maximum=100000)
                db.execute("UPDATE requests SET quote_cents=?,approval_status='pending' WHERE id=?", (cents, request_id))
                self.log(db, request_id, user['name'], 'quote', f'Estimate of £{cents/100:.2f} submitted for customer approval.')
                self.queue_message(db, request_id, f'Your repair estimate is £{cents/100:.2f}. Please contact the workshop to approve or decline.')
            elif action == 'approval':
                self.coordinator(user)
                if data.get('decision') not in ['approved', 'declined']:
                    raise APIError(400, 'Choose approved or declined.')
                if row['approval_status'] != 'pending':
                    raise APIError(409, 'A customer decision can only be recorded for a pending estimate.')
                db.execute('UPDATE requests SET approval_status=? WHERE id=?', (data['decision'], request_id))
                self.log(db, request_id, 'Demo customer', 'approval', f'Customer {data["decision"]} the estimate (simulated).')
            elif action == 'messages':
                self.queue_message(db, request_id, text_field(data, 'body', 2000))
                self.log(db, request_id, user['name'], 'message', 'Customer update queued for the simulated provider.')
            elif action == 'retry-message':
                message_id = integer(data.get('message_id'), 'message_id', maximum=100000000)
                message = db.execute('SELECT * FROM messages WHERE id=? AND request_id=?', (message_id, request_id)).fetchone()
                if not message:
                    raise APIError(404, 'Message not found.')
                if message['status'] != 'failed':
                    raise APIError(409, 'Only failed messages can be retried.')
                db.execute("UPDATE messages SET status='queued',last_error=NULL,updated_at=? WHERE id=?", (now(), message_id))
                self.log(db, request_id, user['name'], 'message', 'Failed message queued for another attempt.')
            else:
                raise APIError(404, 'Action not found.')
            self.touch(db, request_id)
        return {'ok': True}

    def queue_message(self, db, request_id, body):
        timestamp = now()
        db.execute("INSERT INTO messages (request_id,body,status,created_at,updated_at) VALUES (?,?,'queued',?,?)", (request_id, body, timestamp, timestamp))

    def outbox(self, user):
        clause, args = self.scope(user)
        with self.db() as db:
            return [dict(row) for row in db.execute(f'''SELECT m.*,r.reference,r.equipment,r.customer_name
                FROM messages m JOIN requests r ON r.id=m.request_id WHERE {clause} ORDER BY m.id DESC''', args)]

    def process_outbox(self, user, fail_first=False):
        """Explicit demo worker tick: no email leaves this application.

        Accepted means provider acceptance only. We do not receive delivery or read receipts.
        Failed messages require an explicit retry; accepted messages are never resent here.
        """
        self.coordinator(user)
        if not isinstance(fail_first, bool):
            raise APIError(400, 'fail_first must be true or false.')
        processed = 0
        with self.db(write=True) as db:
            messages = db.execute('''SELECT m.* FROM messages m JOIN requests r ON r.id=m.request_id
                WHERE r.organization_id=? AND m.status='queued' ORDER BY m.id''', (user['organization_id'],)).fetchall()
            for index, message in enumerate(messages):
                failed = fail_first and index == 0
                status = 'failed' if failed else 'accepted'
                db.execute('''UPDATE messages SET status=?,attempts=attempts+1,provider_reference=?,last_error=?,updated_at=? WHERE id=?''',
                           (status, None if failed else f'demo-{message["id"]}-{message["attempts"]+1}', 'Simulated provider timeout. Safe to retry.' if failed else None, now(), message['id']))
                self.log(db, message['request_id'], 'Provider simulator', 'message', f'Message #{message["id"]}: {status} by simulated provider.')
                self.touch(db, message['request_id'])
                processed += 1
        return {'processed': processed}
