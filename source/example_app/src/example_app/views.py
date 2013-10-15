from pyramid.view import view_config

@view_config(context=".models.TreeModel", renderer='templates/node.pt')
def node_view(context, request):
    return {'title': context.title, 'body': context.body}
