import logging

from urlparse import urljoin

from django.conf import settings
from django.http import HttpResponseRedirect

from ipware.ip import get_ip

logger = logging.getLogger(__name__)


class HttpResponseTemporaryRedirect(HttpResponseRedirect):
    """
    Redirect the request in a way that it is re-POSTed.
    """
    status_code = 307


def get_production_redirect(request):
    """
    Generate an appropriate redirect to production.
    """
    redirect_url = urljoin(settings.PRODUCTION_URL, request.get_full_path())

    logger.warning('Redirecting production client URL "%s" to "%s"',
                   request.get_full_path(), redirect_url)

    return HttpResponseTemporaryRedirect(redirect_url)


class QueryStringAccessTokenToBearerMiddleware:
    """
    django-oauth-toolkit wants access tokens specified using the
    "Authorization: Bearer" header.
    """
    def process_request(self, request):
        if 'access_token' not in request.GET:
            return

        request.META['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(
            request.GET['access_token'])

        # I don't think access_token should be removed but am leaving this here
        # just in case.
        # request.GET = request.GET.copy()
        # del request.GET['access_token']


class RedirectAmericanGutToProductionMiddleware:
    """
    Redirect a request from American Gut to production.
    """
    def process_request(self, request):
        if get_ip(request) != '128.138.93.14':
            return

        return get_production_redirect(request)


class RedirectStagingToProductionMiddleware:
    """
    Redirect a staging URL to production if it contains a production client ID.
    """
    def process_request(self, request):
        if settings.ENV != 'staging':
            return

        if 'client_id' not in request.GET:
            return

        if request.GET['client_id'] not in settings.PRODUCTION_CLIENT_IDS:
            return

        return get_production_redirect(request)
