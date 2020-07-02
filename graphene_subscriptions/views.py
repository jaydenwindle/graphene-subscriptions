from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
from django.http import Http404
from graphene_django.views import GraphQLView

class GraphQLSubscriptionView(View):
  playground = True

  @method_decorator(ensure_csrf_cookie)
  def get(self, request):
    if self.playground:
      return render(request, 'graphene_subsciptions/playground.html', {"url": request.build_absolute_uri()})

    raise Http404()
  
  @method_decorator(ensure_csrf_cookie)
  def post(self, request):
    return GraphQLView.as_view(graphiql=False)(request)