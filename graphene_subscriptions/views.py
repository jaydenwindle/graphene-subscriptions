from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from graphene_django.views import GraphQLView

@ensure_csrf_cookie
def playground_view(request):
  if request.method == 'GET':
    return render(request, 'graphene_subsciptions/playground.html', {"url": request.build_absolute_uri()})
  elif request.method == 'POST':
    return GraphQLView.as_view(graphiql=False)(request)