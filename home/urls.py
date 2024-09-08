from django.urls import path
from .views import IndexView, AboutUsView, GalleryView, GiftListView, MessageFormView, RSVPFormView


app_name = 'home'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('sobre-nos/', AboutUsView.as_view(), name='about_us'),
    path('galeria/', GalleryView.as_view(), name='gallery'),
    path('presentes/', GiftListView.as_view(), name='gift_list'),
    path('message/', MessageFormView.as_view(), name='message_form'),
    path('confirmar-presenca/', RSVPFormView.as_view(), name='rsvp'),
]