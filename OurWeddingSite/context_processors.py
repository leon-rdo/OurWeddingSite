from home.models import Settings


def settings(request):
    try:
        settings = Settings.objects.get()
    except Settings.DoesNotExist:
        settings = None
    return {'settings': settings}