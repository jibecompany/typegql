from typing import Dict, Tuple

import aiohttp
from graphql import get_introspection_query, build_client_schema, DocumentNode, ExecutionResult

from typegql.client.dsl import DSLSchema


class Client:
    """ Usage:

    async with Client(url) as client:
        await client.introspection()
        dsl = client.dsl
        query = dsl.Query.clients_connection.select(dsl.ClientConnection.total_count)
        doc = dsl.query(query)

        result = await client.execute(doc)
    """
    def __init__(self, url: str, auth=None, headers: Dict = None, use_json=True, timeout=None, camelcase=True):
        self.url = url
        self.session: aiohttp.ClientSession = None
        self.dsl: DSLSchema = None
        self.auth = auth
        self.headers = headers
        self.use_json = use_json
        self.timeout = timeout
        self.camelcase = camelcase

    async def init(self):
        self.session = self.session or aiohttp.ClientSession()

    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self.session.close()

    async def introspection(self):
        status, result = await self.execute(get_introspection_query())
        assert status == 200, f'{status} - {result}'
        schema = build_client_schema(result.data)
        self.dsl = DSLSchema(schema, camelcase=self.camelcase)
        return schema

    async def execute(self, query: str, variable_values=None, timeout=None) -> Tuple[int, ExecutionResult]:
        if isinstance(query, DocumentNode):
            query = self.dsl.as_string(query)

        payload = {
            'query': query,
            'variables': variable_values or {}
        }

        if self.use_json:
            body = {'json': payload}
        else:
            body = {'data': payload}

        async with self.session.post(self.url,
                                     auth=self.auth,
                                     headers=self.headers,
                                     timeout=timeout or self.timeout,
                                     **body) as response:
            result = await response.json() if self.use_json else response.text()
            assert 'errors' in result or 'data' in result, f'Received non-compatible response "{result}"'

            return response.status, ExecutionResult(
                errors=result.get('errors'),
                data=result.get('data')
            )
