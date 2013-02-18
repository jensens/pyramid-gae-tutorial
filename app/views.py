from pyramid.view import view_config

@view_config(route_name='root', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'pyramid_gae_tutorial'}
