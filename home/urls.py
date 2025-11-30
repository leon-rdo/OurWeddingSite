from django.urls import path
from .views import *


app_name = 'home'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('sobre-nos/', AboutUsView.as_view(), name='about_us'),
    path('galeria/', GalleryView.as_view(), name='gallery'),
    path('presentes/', GiftListView.as_view(), name='gift_list'),
    path('cha-de-panela/', BridalShowerGiftListView.as_view(), name='bridal_shower_gift_list'),
    path('message/', MessageFormView.as_view(), name='message_form'),
    path('confirmar-presenca/', RSVPFormView.as_view(), name='rsvp'),
    # URLs do Mercado Pago
    path('payment/create/', CreatePaymentView.as_view(), name='create_payment'),
    path('payment/process/', ProcessPaymentView.as_view(), name='process_payment'),
    path('webhook/mercadopago/', MercadoPagoWebhookView.as_view(), name='mp_webhook'),
    path('payment/status/<int:payment_id>/', PaymentStatusView.as_view(), name='payment_status'),
    path('pagamento/sucesso/', PaymentSuccessView.as_view(), name='payment_success'),
    path('pagamento/falha/', PaymentFailureView.as_view(), name='payment_failure'),
    path('pagamento/pendente/', PaymentPendingView.as_view(), name='payment_pending'),
]