import copy
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from server import handler_for
from traceops.agent import run, SampleGenerator, LiveGenerator, plan, verify
from traceops.connectors import SampleConnector, ZetarisConnector, ConnectorError, validate_origin
from traceops.world import WorldStoreService, IngestPipelineService, ContextBuilderService

class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = WorldStoreService(Path(self.temp.name) / 'world.db')
        self.connector = SampleConnector()
    def tearDown(self):
        self.temp.cleanup()
    def run_question(self, question, connector=None):
        return run(self.store, question, connector or self.connector, SampleGenerator())
    def test_north_expected_totals_and_provenance(self):
        result = self.run_question('Why are orders in the North delayed?')
        self.assertEqual(result['metrics']['delayed_orders'], 4)
        self.assertEqual(result['metrics']['order_value_at_risk'], 3600)
        self.assertEqual(result['metrics']['units_affected'], 30)
        self.assertEqual({f['certainty'] for f in result['findings']}, {'corroborated', 'inferred'})
        citations = {e['citation'] for e in result['evidence']}
        self.assertTrue(all(set(f['citations']) <= citations for f in result['findings']))
        self.assertTrue(all(not a['external_action'] for a in result['actions']))
        self.assertEqual(len(self.store.events(result['id'])), 6)
    def test_all_orders_and_single_carrier(self):
        result = self.run_question('Investigate all delayed orders')
        self.assertEqual(result['metrics']['delayed_orders'], 6)
        self.assertEqual(result['metrics']['order_value_at_risk'], 4350)
        single = self.run_question('Why is ORD-1045 delayed?')
        self.assertEqual(len(single['findings']), 1)
        self.assertEqual(single['findings'][0]['certainty'], 'documented')
        self.assertIn('carrier', single['findings'][0]['explanation'])
    def test_empty_scope_not_fake_success(self):
        result = self.run_question('Why is ORD-9999 delayed?')
        self.assertEqual(result['findings'], [])
        self.assertTrue(result['warnings'])
    def test_ingest_is_idempotent_and_snapshot_isolated(self):
        sources = self.connector.fetch()
        self.store.start('a', 'a')
        ingest = IngestPipelineService(self.store)
        ingest.ingest('a', sources, 'sample')
        first = self.store.health()['observations']
        ingest.ingest('a', sources, 'sample')
        self.assertEqual(self.store.health()['observations'], first)
        changed = copy.deepcopy(sources)
        changed['orders'][0]['status'] = 'shipped'
        self.store.start('b', 'b')
        ingest.ingest('b', changed, 'sample')
        context = ContextBuilderService(self.store)
        self.assertEqual(context.build('a', order_id='ORD-1041')['orders'][0]['record']['status'], 'delayed')
        self.assertEqual(context.build('b', order_id='ORD-1041')['orders'][0]['record']['status'], 'shipped')
        reopened = WorldStoreService(self.store.path)
        self.assertEqual(ContextBuilderService(reopened).build('a', order_id='ORD-1041')['orders'][0]['record']['status'], 'delayed')
    def test_missing_inventory_is_unknown(self):
        class Missing(SampleConnector):
            def fetch(self):
                data = super().fetch(); data['inventory'] = []; data['tickets'] = []; return data
        result = self.run_question('Investigate order ORD-1041', Missing())
        self.assertEqual(result['findings'][0]['certainty'], 'unknown')
    def test_conflicting_ticket_is_visible(self):
        class Conflict(SampleConnector):
            def fetch(self):
                data = super().fetch(); data['tickets'][0]['category'] = 'carrier'; return data
        result = self.run_question('Investigate order ORD-1041', Conflict())
        self.assertIn('different blocker', result['findings'][0]['explanation'])
    def test_duplicate_keys_roll_back_snapshot(self):
        data = self.connector.fetch(); data['orders'].append(data['orders'][0]); self.store.start('dup', 'dup')
        with self.assertRaises(ValueError):
            IngestPipelineService(self.store).ingest('dup', data, 'sample')
        self.assertEqual(self.store.health()['observations'], 0)
    def test_provider_failure_never_falls_back(self):
        class Broken(SampleConnector):
            mode = 'zetaris'
            def fetch(self):
                raise ConnectorError('Unavailable')
        with self.assertRaises(ConnectorError):
            self.run_question('Investigate all delayed orders', Broken())
        self.assertEqual(self.store.history()[0]['status'], 'failed')
        self.assertEqual(self.store.health()['observations'], 0)
    def test_unknown_question_and_bad_citations_rejected(self):
        with self.assertRaises(ValueError):
            plan('Tell me about the weather')
        with self.assertRaises(ValueError):
            verify({'orders': [], 'inventory': [], 'tickets': []}, [{'citations': ['fake']}])
    def test_zetaris_request_contract(self):
        self.assertEqual(ZetarisConnector.normalize({'data': {'columns': [{'name': 'x'}], 'rows': [[1]]}}), [{'x': 1}])
        with self.assertRaises(ConnectorError):
            ZetarisConnector.normalize({'surprise': 'not data'})
        with patch.dict(os.environ, {'ZETARIS_BASE_URL': 'http://localhost:3000', 'ZETARIS_ORG_ID': '1', 'ZETARIS_API_KEY': 'test'}):
            with patch('traceops.connectors.post_json') as call:
                call.side_effect = [self.connector.fetch()[t] for t in ('orders', 'inventory', 'tickets')]
                self.assertEqual(len(ZetarisConnector().fetch()['orders']), 12)
                self.assertEqual(call.call_args_list[0].args[0], 'http://localhost:3000/api/proxy/sql-editor/sqls/run-query')
                self.assertEqual(call.call_args_list[0].args[1]['sql'], 'SELECT * FROM traceops.orders LIMIT 1001')
    def test_live_generator_validates_citations(self):
        context = {'scope': {}}
        findings = [{'citations': ['a' * 24], 'explanation': 'Source says delayed.'}]
        with patch.dict(os.environ, {'MODEL_API_KEY': 'test', 'MODEL_NAME': 'test-model'}):
            with patch('traceops.agent.post_json') as call:
                call.return_value = {'choices': [{'message': {'content': json.dumps({'text': 'Delayed [' + 'a' * 24 + ']'})}}], 'usage': {'total_tokens': 20}}
                out = LiveGenerator().generate(context, findings)
                self.assertEqual(out['usage']['total_tokens'], 20)
                call.return_value = {'choices': [{'message': {'content': json.dumps({'text': 'Invented [' + 'b' * 24 + ']'})}}]}
                with self.assertRaises(ConnectorError):
                    LiveGenerator().generate(context, findings)
    def test_truncated_context_is_explicit(self):
        sources = self.connector.fetch()
        self.store.start('truncated', 'all orders')
        IngestPipelineService(self.store).ingest('truncated', sources, 'sample')
        context = ContextBuilderService(self.store).build('truncated', limit=2)
        self.assertTrue(context['truncated'])
        self.assertEqual(len(context['orders']), 2)
    def test_remote_http_credentials_disallowed(self):
        for url in ('http://example.com', 'https://key:secret@example.com', 'https://example.com?key=secret'):
            with self.assertRaises(ConnectorError):
                validate_origin(url)
    def test_http_end_to_end_and_origin_guard(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store))
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with patch.dict(os.environ, {'TRACEOPS_DATA_MODE': 'sample', 'TRACEOPS_MODEL_MODE': 'sample'}):
                req = Request(base + '/api/investigate', data=json.dumps({'question': 'Why are North orders delayed?'}).encode(), headers={'Content-Type': 'application/json'})
                with urlopen(req) as response:
                    result = json.load(response)
                with urlopen(base + '/api/runs/' + result['id'] + '/trace') as response:
                    events = [json.loads(l) for l in response.read().decode().splitlines()]
                self.assertEqual(events[-1]['kind'], 'run.completed')
                req = Request(base + '/api/investigate', data=b'{}', headers={'Origin': 'https://evil.example'})
                with self.assertRaises(HTTPError) as error:
                    urlopen(req)
                self.assertEqual(error.exception.code, 403)
                with self.assertRaises(HTTPError):
                    urlopen(base + '/.env.local')
        finally:
            server.shutdown(); server.server_close(); worker.join()

if __name__ == '__main__':
    unittest.main()
