"""Read-only data adapters. Live errors are never replaced by sample data."""
import csv
import json
import os
import re
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TABLES = ('orders', 'inventory', 'tickets')
REQUIRED = {
    'orders': {'order_id', 'customer', 'region', 'sku', 'quantity', 'order_value', 'status', 'promised_date', 'updated_at'},
    'inventory': {'sku', 'product', 'warehouse', 'available_units', 'inbound_date', 'inbound_status', 'updated_at'},
    'tickets': {'ticket_id', 'order_id', 'category', 'message', 'updated_at'},
}


class ConnectorError(Exception):
    pass


def validate_origin(url):
    p = urlparse(url)
    if p.username or p.password or p.query or p.fragment:
        raise ConnectorError('Provider URL must not contain credentials, query, or fragment.')
    if p.scheme != 'https' and not (p.scheme == 'http' and p.hostname in ('localhost', '127.0.0.1', '::1')):
        raise ConnectorError('Provider URL requires HTTPS (HTTP is allowed only on loopback).')
    return url.rstrip('/')


def post_json(url, body, headers):
    request = Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **headers}, method='POST')
    try:
        with urlopen(request, timeout=40) as response:
            return json.load(response)
    except HTTPError as exc:
        raise ConnectorError(f'Provider returned HTTP {exc.code}; check server-side credentials and endpoint.') from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise ConnectorError('Provider request failed; check connectivity and JSON response format.') from None


def validate_rows(table, rows):
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ConnectorError(f'{table}: expected an array of objects.')
    if len(rows) > 1000:
        raise ConnectorError(f'{table}: exceeds the 1000-row MVP limit; narrow your virtual view.')
    for row in rows:
        if not REQUIRED[table].issubset(row):
            raise ConnectorError(f'{table}: missing required columns: {sorted(REQUIRED[table] - set(row))}')
    return rows


class SampleConnector:
    mode = 'sample'

    def fetch(self):
        result = {}
        for table in TABLES:
            with (ROOT / 'data' / f'{table}.csv').open(newline='', encoding='utf-8') as f:
                result[table] = validate_rows(table, list(csv.DictReader(f)))
        return result


class ZetarisConnector:
    mode = 'zetaris'

    def __init__(self):
        self.base = validate_origin(os.getenv('ZETARIS_BASE_URL', 'http://localhost:3000'))
        if urlparse(self.base).path not in ('', '/'):
            raise ConnectorError('ZETARIS_BASE_URL must be the UI origin without a path.')
        self.key = os.getenv('ZETARIS_API_KEY', '')
        self.org = os.getenv('ZETARIS_ORG_ID', '')
        if not self.key or not self.org.isdigit():
            raise ConnectorError('Live data mode requires ZETARIS_API_KEY and numeric ZETARIS_ORG_ID in .env.local.')

    def fetch(self):
        result = {}
        for table in TABLES:
            name = os.getenv(f'ZETARIS_{table.upper()}_TABLE', f'traceops.{table}')
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){0,2}', name):
                raise ConnectorError('Invalid virtual table identifier in server configuration.')
            body = {'sql': f'SELECT * FROM {name} LIMIT 1001', 'limit': 1001}
            if os.getenv('ZETARIS_ENGINE_ID'):
                body['engineId'] = os.environ['ZETARIS_ENGINE_ID']
            raw = post_json(self.base + '/api/proxy/sql-editor/sqls/run-query', body, {
                'Authorization': 'Bearer ' + self.key, 'X-Org-ID': self.org, 'X-Request-ID': str(uuid.uuid4())})
            result[table] = validate_rows(table, self.normalize(raw))
        return result

    @staticmethod
    def normalize(raw):
        # Known proxy deployments vary. Reject unknown responses rather than guessing.
        data = raw.get('data', raw) if isinstance(raw, dict) else raw
        if isinstance(data, dict):
            rows = data.get('rows', data.get('results'))
            columns = data.get('columns')
            if isinstance(rows, list) and rows and isinstance(rows[0], list) and isinstance(columns, list):
                names = [c['name'] if isinstance(c, dict) else c for c in columns]
                if any(len(r) != len(names) for r in rows):
                    raise ConnectorError('Zetaris column/row lengths differ.')
                return [dict(zip(names, r)) for r in rows]
            if rows is not None:
                return rows
        if isinstance(data, list):
            return data
        raise ConnectorError('Unknown Zetaris response shape; verify tenant proxy output and update normalize().')


def get_connector():
    mode = os.getenv('TRACEOPS_DATA_MODE', 'sample')
    if mode == 'sample':
        return SampleConnector()
    if mode == 'zetaris':
        return ZetarisConnector()
    raise ConnectorError('TRACEOPS_DATA_MODE must be sample or zetaris.')
