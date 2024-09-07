from django.urls import path
from .views import IndexView, AboutUsView, GalleryView
from django.conf import settings
from django.conf.urls.static import static

app_name = 'home'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('sobre-nos/', AboutUsView.as_view(), name='about_us'),
    path('galeria/', GalleryView.as_view(), name='gallery'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)