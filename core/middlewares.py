import logging
import sys
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.debug import ExceptionReporter
from django.http import Http404

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            response = self.get_response(request)
            return self.process_response(request, response)
        except Exception as e:
            return self.process_exception(request, e)

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        # Skip admin, auth, and error template responses
        if (
            request.path.startswith("/admin/") or
            request.path.startswith("/auth/") or
            (hasattr(response, "template_name") and 
             isinstance(response.template_name, str) and
             response.template_name.startswith("errors/"))
        ):
            return response

        # Handle 4xx errors
        if 400 <= response.status_code < 500:
            logger.warning(
                f"Client error {response.status_code} in "
                f"{request.method} {request.path}",
                extra={
                    "request": request,
                    "status_code": response.status_code,
                },
            )
            try:
                return render(
                    request,
                    "errors/400.html",
                    {"status_code": response.status_code},
                    status=response.status_code,
                )
            except Exception as e:
                logger.error(f"Error rendering 400 template: {str(e)}")
                return response

        # Handle 5xx errors
        elif 500 <= response.status_code < 600:
            logger.error(
                f"Server error {response.status_code} in "
                f"{request.method} {request.path}",
                extra={
                    "request": request,
                    "status_code": response.status_code,
                },
            )
            try:
                return render(
                    request,
                    "errors/500.html",
                    {"status_code": response.status_code},
                    status=response.status_code,
                )
            except Exception as e:
                logger.error(f"Error rendering 500 template: {str(e)}")
                return response

        return response

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        # Skip admin and auth requests
        if request.path.startswith("/admin/") or request.path.startswith("/auth/"):
            return None

        # Handle Http404 exceptions
        if isinstance(exception, Http404):
            logger.warning(
                f"Page not found: {request.method} {request.path}",
                extra={
                    "request": request,
                    "status_code": 404,
                },
            )
            try:
                return render(
                    request,
                    "errors/400.html",
                    {"status_code": 404},
                    status=404,
                )
            except Exception as e:
                logger.error(f"Error rendering 404 template: {str(e)}")
                return HttpResponse("Not Found", status=404)

        # Log the full exception details for other exceptions
        reporter = ExceptionReporter(request, is_email=False, *sys.exc_info())
        logger.error(
            f"Unhandled exception in {request.method} {request.path}",
            extra={
                "request": request,
                "exception": str(exception),
                "traceback": reporter.get_traceback_text(),
            },
        )

        try:
            return render(
                request,
                "errors/500.html",
                {"status_code": 500},
                status=500,
            )
        except Exception as e:
            logger.error(f"Error rendering 500 template: {str(e)}")
            return HttpResponse("Internal Server Error", status=500)


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.get_response(request)

        if (
            not request.user.password_redefined
            and request.path != "/force-password-change/"
            and not request.path.startswith("/static/")
            and not request.path.startswith("/media/")
        ):
            from django.shortcuts import redirect

            return redirect("force-password-change")

        return self.get_response(request)
