from django.conf.urls import url
from . import views
from django.views.generic import TemplateView
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings
from django.conf.urls import include, url
import debug_toolbar


#
# Gestion du 404
#
def handler404(request):
    response = render_to_response('404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response


urlpatterns = [
    url(r'^$', views.dashboard_view, name='dashboard'),
    url(r'^connexions/$', views.connexions_view, name='connexions'),
    url(r'^consultations/$', views.consultations_view, name='consultations'),
    url(r'^params', views.params_view, name='params'),

    url(r'^editeurs/$', views.editeurs_view, name='editeurs'),
    url(r'^editeur/(?P<slug>[\w\-]+)/$', views.editeur_view, name='editeur'),

    url(r'^ressources/$', views.ressources_view, name='ressources'),
    url(r'^ressource/(?P<slug>[\w\-]+)/$', views.ressource_view, name='ressource'),

    url(r'^lien/(?P<slug>[\w\-]+)?/$', views.lien_view, name='lien'),

    url(r'^login$', views.login_view, name='login'),
    url(r'^logout$', views.logout_view, name='logout'),

    url(r'^__debug__/', include(debug_toolbar.urls)),
]