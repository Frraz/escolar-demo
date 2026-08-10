from .models import GoogleCredential


def drive_status(request):
    if not request.user.is_authenticated:
        return {}
    return {"drive_connected": GoogleCredential.get_solo() is not None}
