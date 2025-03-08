from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if (not request.user.password_redefined) and (request.path != reverse("force-password-change")):
                return redirect("force-password-change")
        response = self.get_response(request)
        return response