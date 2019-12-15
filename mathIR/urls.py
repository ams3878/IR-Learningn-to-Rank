from django.urls import path
from .views import results, home, main


urlpatterns = [
    path('', home, name='home'),
    path('results', results, name='results'),
    path('main', main, name='main')
]
