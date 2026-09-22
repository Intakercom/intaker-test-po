"""Fictional fixtures. Dates are relative to first run; IDs stay stable."""
import json
from datetime import datetime, timedelta, timezone


def seed(db):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    def ago(hours):
        return (now - timedelta(hours=hours)).isoformat().replace('+00:00', 'Z')

    db.executemany('INSERT INTO organizations VALUES (?,?)', [
        ('benchside', 'Benchside Repair Collective'),
        ('northstar', 'Northstar Fixing Club'),
    ])
    db.executemany('INSERT INTO users VALUES (?,?,?,?,?)', [
        ('alex', 'benchside', 'Alex Morgan', 'coordinator', '[]'),
        ('sam', 'benchside', 'Sam Rivera', 'technician', json.dumps(['lighting', 'appliances'])),
        ('jules', 'benchside', 'Jules Chen', 'technician', json.dumps(['sewing', 'audio'])),
        ('robin', 'northstar', 'Robin Ellis', 'coordinator', '[]'),
    ])
    # ref, customer, equipment, category, description, priority, status, owner,
    # estimated minutes, quote cents, approval, age hours, last update hours
    rows = [
        (1042, 'Nora Patel', 'Anglepoise desk lamp', 'lighting', 'The light flickers when the arm moves. This belonged to my grandmother; please keep the original shade.', 'high', 'queued', 'sam', 45, 2500, 'pending', 120, 4),
        (1041, 'Emilia Brooks', 'Singer sewing machine', 'sewing', 'The needle moves but the feed dogs do not pull the fabric through. Model 4423.', 'normal', 'queued', 'jules', 90, 4000, 'approved', 144, 8),
        (1040, 'Theo Martin', 'KitchenAid hand mixer', 'appliances', 'Runs at one speed only. Both beaters are included.', 'normal', 'new', None, None, None, 'not_requested', 5, 5),
        (1039, 'Ada Wilson', 'Roberts portable radio', 'audio', 'Crackling on both channels after ten minutes. Mains power works; battery compartment is clean.', 'normal', 'assessing', 'jules', 60, None, 'not_requested', 48, 3),
        (1038, 'Owen Clarke', 'Dualit toaster', 'appliances', 'Left slot does not heat. Customer is happy with a functional repair and cosmetic wear.', 'high', 'queued', 'sam', 60, 3000, 'approved', 192, 6),
        (1037, 'Iris Lewis', 'Brass reading lamp', 'lighting', 'Switch has become stiff. Check the cable and switch together.', 'normal', 'repairing', 'sam', 30, 1800, 'approved', 72, 1),
        (1036, 'Ravi Shah', 'Brother overlocker', 'sewing', 'Thread snaps on the lower loop. Bring back with the original accessories.', 'normal', 'ready', 'jules', 60, 3500, 'approved', 168, 2),
        (1035, 'Maya Green', 'Bodum coffee grinder', 'appliances', 'Motor hums but the blade does not turn. No visible obstruction.', 'normal', 'assessing', None, 45, None, 'not_requested', 30, 12),
        (1034, 'Felix Reed', 'Yamaha bookshelf speaker', 'audio', 'One speaker has intermittent sound. Customer supplied a matching working speaker for comparison.', 'normal', 'queued', 'jules', 60, 2800, 'approved', 240, 18),
        (1033, 'Lena Wood', 'Ceramic bedside lamp', 'lighting', 'Loose bulb holder. Customer has approved replacement with a matching finish.', 'normal', 'queued', None, 30, 1500, 'approved', 96, 10),
        (1032, 'Ben Foster', 'Janome sewing machine', 'sewing', 'Timing is out after a needle broke. Customer declined the quoted repair.', 'normal', 'assessing', 'jules', 120, 6500, 'declined', 216, 24),
        (1031, 'Sofia Evans', 'Russell Hobbs kettle', 'appliances', 'Lid latch repaired and tested. Collected by customer.', 'normal', 'closed', 'sam', 30, 1200, 'approved', 288, 48),
        (1030, 'Leo King', 'Vintage transistor radio', 'audio', 'Customer decided to collect the item without repair.', 'normal', 'cancelled', 'jules', None, None, 'not_requested', 312, 72),
        (1029, 'Grace Hall', 'Philips table lamp', 'lighting', 'Needs a new plug and cable inspection.', 'normal', 'new', None, None, None, 'not_requested', 2, 2),
    ]
    for ref, customer, equipment, category, description, priority, status, owner, estimate, quote, approval, age, updated in rows:
        db.execute('''INSERT INTO requests
            (id,reference,organization_id,customer_name,customer_email,equipment,category,description,priority,status,assigned_to,estimated_minutes,quote_cents,approval_status,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (ref, f'BS-{ref}', 'benchside', customer, customer.lower().replace(' ', '.')+'@example.test', equipment, category, description, priority, status, owner, estimate, quote, approval, ago(age), ago(updated)))
        db.execute('INSERT INTO activity (request_id,actor,event_type,message,created_at) VALUES (?,?,?,?,?)',
                   (ref, 'Front desk', 'created', 'Repair request received at the workshop.', ago(age)))
        if owner:
            db.execute('INSERT INTO activity (request_id,actor,event_type,message,created_at) VALUES (?,?,?,?,?)',
                       (ref, 'Alex Morgan', 'assigned', f'Assigned to {"Sam Rivera" if owner == "sam" else "Jules Chen"}.', ago(age-1)))
        if approval != 'not_requested':
            db.execute('INSERT INTO activity (request_id,actor,event_type,message,created_at) VALUES (?,?,?,?,?)',
                       (ref, 'Demo customer' if approval != 'pending' else 'Alex Morgan', 'approval', f'Customer approval: {approval}.', ago(updated)))
    for request_id, name, quantity, status in [
        (1042, 'Fabric-covered flex', 1, 'received'),
        (1041, 'Feed gear assembly', 1, 'ordered'),
        (1038, 'Heating element', 1, 'received'),
        (1037, 'Inline switch', 1, 'received'),
        (1034, 'Speaker terminal pair', 1, 'needed'),
    ]:
        db.execute('INSERT INTO parts (request_id,name,quantity,status,updated_at) VALUES (?,?,?,?,?)',
                   (request_id, name, quantity, status, ago(6)))
    db.execute('''INSERT INTO requests
        (id,reference,organization_id,customer_name,customer_email,equipment,category,description,priority,status,assigned_to,estimated_minutes,approval_status,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (2001, 'NS-2001', 'northstar', 'Jamie Stone', 'jamie@example.test', 'Northstar workshop lamp', 'lighting', 'A separate organization fixture.', 'normal', 'new', None, 30, 'not_requested', ago(24), ago(24)))
    for request_id, body, status, age, error in [
        (1042, 'Your repair estimate is £25. Please let us know whether you would like us to proceed.', 'accepted', 20, None),
        (1036, 'Your overlocker is ready for collection during workshop hours.', 'failed', 2, 'Simulated provider timeout. Safe to retry.'),
        (1041, 'We are waiting for a replacement feed gear before starting the repair.', 'queued', 1, None),
    ]:
        db.execute('''INSERT INTO messages
            (request_id,body,status,attempts,provider_reference,last_error,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?)''',
            (request_id, body, status, 0 if status == 'queued' else 1, 'demo-provider-001' if status == 'accepted' else None, error, ago(age), ago(age)))
    db.execute('INSERT INTO imported_events VALUES (?,?,?)', ('benchside', 'sample-dropoff-001', 1040))
