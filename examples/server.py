import logging

from graphql import GraphQLError
from sanic import Sanic
from sanic.response import json, html

from aiograph.core.schema import Schema
from examples.library.query import Query

from examples.library.template import TEMPLATE

logger = logging.getLogger('sanic.error')
app = Sanic()
schema = Schema(Query)


@app.route('', methods=['GET'])
async def default(request):
    return html(TEMPLATE)


@app.route('/graphql', methods=['POST'])
async def default(request):
    query = request.args.get('query') if request.method.lower() == 'get' else request.json.get('query')
    try:
        result = await schema.run(query, Query())
    except GraphQLError as e:
        logger.exception(e)
        return json({'data': str(e)})
    if result.errors:
        for error in result.errors:
            logger.exception(error)
        return json({'data': [str(e) for e in result.errors]}, status=401)
    return json({'data': result.data})


if __name__ == '__main__':
    app.run(host='localhost', port=3000, debug=True, auto_reload=False)
