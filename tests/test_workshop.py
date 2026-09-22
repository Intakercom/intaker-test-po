"""Behavior tests for the demo's product rules, access boundaries and API."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from backend.database import initialize
from backend.service import Workshop, APIError
from backend.server import create_server


class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'workshop.sqlite3'
        initialize(self.path)
        self.workshop = Workshop(self.path)
        self.alex = self.workshop.user('alex')
        self.sam = self.workshop.user('sam')
        self.jules = self.workshop.user('jules')
        self.robin = self.workshop.user('robin')

    def tearDown(self):
        self.temp.cleanup()

    def assert_error(self, status, fn, *args):
        with self.assertRaises(APIError) as caught:
            fn(*args)
        self.assertEqual(caught.exception.status, status)

    def payload(self):
        return {'customer_name':'Test Customer','customer_email':'test@example.test','equipment':'Test lamp','category':'lighting','description':'A loose switch.','priority':'normal'}

    def version(self, request_id=1042):
        return self.workshop.detail(self.alex, request_id)['version']

    def action(self, action, data, request_id=1042, user=None):
        return self.workshop.action(user or self.alex, request_id, action, {**data,'version':self.version(request_id)})

    def test_seed_counts_and_initialize_is_idempotent(self):
        initialize(self.path)
        self.assertEqual(len(self.workshop.list_requests(self.alex)),14)
        self.assertEqual(self.workshop.dashboard(self.alex)['active'],12)
        self.assertEqual(self.workshop.dashboard(self.alex)['waiting_parts'],2)
        self.assertEqual(self.workshop.dashboard(self.alex)['approval_pending'],1)

    def test_organization_isolation(self):
        self.assertEqual([r['id'] for r in self.workshop.list_requests(self.robin)],[2001])
        self.assert_error(404,self.workshop.detail,self.alex,2001)
        self.assert_error(404,self.workshop.detail,self.robin,1042)
        self.assertEqual(self.workshop.outbox(self.robin),[])

    def test_technician_sees_only_assigned_records(self):
        self.assertTrue(all(r['assigned_to']=='sam' for r in self.workshop.list_requests(self.sam)))
        self.assert_error(404,self.workshop.detail,self.sam,1041)
        self.assert_error(404,self.workshop.action,self.sam,1041,'notes',{'version':1,'body':'No access'})

    def test_reassignment_changes_access_and_preserves_history(self):
        self.workshop.update(self.alex,1042,{'version':1,'assigned_to':'jules'})
        self.assert_error(404,self.workshop.detail,self.sam,1042)
        detail=self.workshop.detail(self.jules,1042)
        self.assertEqual(detail['assigned_to'],'jules')
        self.assertEqual(len(detail['messages']),1)
        self.assertTrue(any('Jules Chen' in a['message'] for a in detail['activity']))

    def test_technician_cannot_assign_or_change_priority(self):
        self.assert_error(403,self.workshop.update,self.sam,1042,{'version':1,'assigned_to':'jules'})
        self.assert_error(403,self.workshop.update,self.sam,1042,{'version':1,'priority':'normal'})
        self.assert_error(403,self.workshop.create,self.sam,self.payload())

    def test_cannot_assign_coordinator_or_another_organization(self):
        for user_id in ['alex','robin','missing']:
            self.assert_error(400,self.workshop.update,self.alex,1042,{'version':1,'assigned_to':user_id})

    def test_stale_version_preserves_first_edit(self):
        self.workshop.update(self.alex,1042,{'version':1,'status':'assessing'})
        self.assert_error(409,self.workshop.update,self.alex,1042,{'version':1,'status':'closed'})
        self.assertEqual(self.workshop.detail(self.alex,1042)['status'],'assessing')
        self.assert_error(409,self.workshop.update,self.alex,1042,{'version':True,'status':'closed'})

    def test_failed_edit_rolls_back_all_fields(self):
        self.assert_error(400,self.workshop.update,self.alex,1042,{'version':1,'status':'closed','estimated_minutes':-5})
        self.assertEqual(self.workshop.detail(self.alex,1042)['status'],'queued')
        self.assertEqual(self.version(),1)

    def test_workflow_and_approval_are_independent(self):
        self.workshop.update(self.sam,1042,{'version':1,'status':'repairing'})
        row=self.workshop.detail(self.alex,1042)
        self.assertEqual(row['status'],'repairing')
        self.assertEqual(row['approval_status'],'pending')

    def test_quote_resets_approval_and_queues_message(self):
        self.action('quote',{'quote_cents':4500},1041)
        row=self.workshop.detail(self.alex,1041)
        self.assertEqual(row['approval_status'],'pending')
        self.assertEqual(row['quote_cents'],4500)
        self.assertEqual(row['messages'][0]['status'],'queued')
        self.assertIn('£45.00',row['messages'][0]['body'])
        self.assertEqual(row['status'],'queued')

    def test_customer_decision_requires_pending_quote(self):
        self.action('approval',{'decision':'approved'})
        self.assert_error(409,self.action,'approval',{'decision':'declined'})
        self.assert_error(403,self.action,'quote',{'quote_cents':1000},1042,self.sam)

    def test_part_status_is_request_scoped(self):
        part=self.workshop.detail(self.alex,1041)['parts'][0]
        self.assert_error(404,self.action,'part-status',{'part_id':part['id'],'status':'received'})
        self.action('part-status',{'part_id':part['id'],'status':'received'},1041)
        self.assertEqual(self.workshop.dashboard(self.alex)['waiting_parts'],1)

    def test_duplicate_import_is_idempotent(self):
        first=self.workshop.create(self.alex,self.payload(),'unique-import')
        second=self.workshop.create(self.alex,{},'unique-import')
        self.assertEqual(first['id'],second['id'])
        self.assertTrue(second['duplicate'])
        self.assertEqual(len(self.workshop.list_requests(self.alex)),15)

    def test_import_event_keys_are_organization_scoped(self):
        other=self.workshop.create(self.robin,self.payload(),'sample-dropoff-001')
        original=self.workshop.create(self.alex,{},'sample-dropoff-001')
        self.assertNotEqual(other['id'],original['id'])
        self.assertEqual(original['id'],1040)

    def test_invalid_request_does_not_write_partial_data(self):
        for field,value in [('customer_email','broken'),('category','cars'),('priority','urgent'),('description','')]:
            self.assert_error(400,self.workshop.create,self.alex,{**self.payload(),field:value})
        self.assertEqual(len(self.workshop.list_requests(self.alex)),14)

    def test_notes_are_persisted_as_plain_text(self):
        body='<script>alert("test")</script>'
        self.action('notes',{'body':body})
        self.assertEqual(self.workshop.detail(self.alex,1042)['activity'][0]['message'],body)

    def test_outbox_worker_accepts_only_queued_and_does_not_resend(self):
        self.assertEqual(self.workshop.process_outbox(self.alex)['processed'],1)
        self.assertEqual(self.workshop.process_outbox(self.alex)['processed'],0)
        self.assertEqual(self.workshop.detail(self.alex,1041)['messages'][0]['status'],'accepted')
        self.assertEqual(self.workshop.detail(self.alex,1036)['messages'][0]['status'],'failed')

    def test_simulated_timeout_explicit_retry_and_attempt_count(self):
        self.workshop.process_outbox(self.alex,True)
        msg=self.workshop.detail(self.alex,1041)['messages'][0]
        self.assertEqual(msg['status'],'failed')
        self.action('retry-message',{'message_id':msg['id']},1041)
        self.workshop.process_outbox(self.alex)
        retried=self.workshop.detail(self.alex,1041)['messages'][0]
        self.assertEqual(retried['status'],'accepted')
        self.assertEqual(retried['attempts'],2)
        self.assert_error(409,self.action,'retry-message',{'message_id':msg['id']},1041)

    def test_provider_tick_cannot_process_another_organization(self):
        self.assertEqual(self.workshop.process_outbox(self.robin)['processed'],0)
        self.assertEqual(self.workshop.detail(self.alex,1041)['messages'][0]['status'],'queued')
        self.assert_error(403,self.workshop.process_outbox,self.sam)

    def test_unknown_user_and_bad_types(self):
        self.assert_error(401,self.workshop.user,'unknown')
        self.assert_error(400,self.action,'parts',{'name':'Switch','quantity':True})
        self.assert_error(400,self.workshop.process_outbox,self.alex,'yes')
        self.assert_error(400,self.workshop.update,self.alex,1042,{'version':1,'organization_id':'northstar'})


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        path=Path(cls.temp.name)/'http.sqlite3'
        initialize(path)
        cls.server=create_server(Workshop(path),0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()

    def request(self,path,method='GET',data=None,headers=None):
        header={'Content-Type':'application/json',**(headers or {})}
        req=Request(self.base+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers=header)
        try:
            response=urlopen(req,timeout=5)
        except HTTPError as error:
            response=error
        with response:
            return response.status,response.headers,response.read()

    def test_frontend_and_health_are_served(self):
        for path in ['/','/styles.css','/app.js','/mark.svg','/api/health']:
            status,headers,body=self.request(path)
            self.assertEqual(status,200)
            self.assertTrue(body)
            self.assertIn('frame-ancestors',headers['Content-Security-Policy'])

    def test_api_profile_enforced(self):
        status,_,body=self.request('/api/requests/1041',headers={'X-Demo-User':'sam'})
        self.assertEqual(status,404)
        self.assertIn('error',json.loads(body))

    def test_create_roundtrip(self):
        payload={'customer_name':'HTTP Customer','customer_email':'http@example.test','equipment':'HTTP lamp','category':'lighting','description':'Switch repair'}
        status,_,body=self.request('/api/requests','POST',payload)
        self.assertEqual(status,201)
        new_id=json.loads(body)['id']
        self.assertEqual(self.request(f'/api/requests/{new_id}')[0],200)

    def test_cross_origin_write_rejected(self):
        status,_,_=self.request('/api/outbox/process','POST',{}, {'Origin':'https://unrelated.example'})
        self.assertEqual(status,403)

    def test_static_path_cannot_escape_frontend(self):
        self.assertEqual(self.request('/%2e%2e/backend/schema.sql')[0],404)
        self.assertEqual(self.request('/run.py')[0],404)

    def test_bad_payload_and_unknown_endpoint_are_json_errors(self):
        self.assertEqual(self.request('/api/imports/dropoff','POST',{})[0],400)
        self.assertEqual(self.request('/api/unknown')[0],404)
        self.assertEqual(self.request('/api/requests','POST',[])[0],400)


if __name__=='__main__':
    unittest.main()
