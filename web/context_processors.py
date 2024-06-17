from django.utils import translation

def bidi(request):
    return {
        'LANGUAGE_BIDI': translation.get_language_bidi(),
    }
