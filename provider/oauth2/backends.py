from base64 import standard_b64decode

from ..utils import now
from .forms import ClientAuthForm, PublicPasswordGrantForm
from .models import AccessToken


class BaseBackend(object):
    """
    Base backend used to authenticate clients as defined in :rfc:`1` against
    our database.
    """
    def authenticate(self, request=None):
        """
        Override this method to implement your own authentication backend.
        Return a client or ``None`` in case of failure.
        """
        pass


class BasicClientBackend(object):
    """
    Backend that tries to authenticate a client through HTTP authorization
    headers as defined in :rfc:`2.3.1`.
    """
    def authenticate(self, request=None):
        auth = request.META.get('HTTP_AUTHORIZATION')

        if auth is None or auth == '':
            return None

        try:
            basic, base64_str = auth.split(' ')
            base64_bytes = standard_b64decode(base64_str)
            try:
                base64_str = base64_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # the token was not a correctly-formed base64-string,
                # which means that this backend shall not proceed further.
                return None

            client_id, client_secret = base64_str.split(':')

            form = ClientAuthForm({
                'client_id': client_id,
                'client_secret': client_secret})

            if form.is_valid():
                return form.cleaned_data.get('client')
            return None

        except ValueError:
            # Auth header was malformed, unpacking went wrong
            return None


class RequestParamsClientBackend(object):
    """
    Backend that tries to authenticate a client through request parameters
    which might be in the request body or URI as defined in :rfc:`2.3.1`.
    """
    def authenticate(self, request=None):
        if request is None:
            return None

        form = ClientAuthForm(request.REQUEST)

        if form.is_valid():
            return form.cleaned_data.get('client')

        return None


class PublicPasswordBackend(object):
    """
    Backend that tries to authenticate a client using username, password
    and client ID. This is only available in specific circumstances:

     - grant_type is "password"
     - client.client_type is 'public'
    """

    def authenticate(self, request=None):
        if request is None:
            return None

        form = PublicPasswordGrantForm(request.REQUEST)

        if form.is_valid():
            return form.cleaned_data.get('client')

        return None


class AccessTokenBackend(object):
    """
    Authenticate a user via access token and client object.
    """

    def authenticate(self, access_token=None, client=None):
        try:
            return AccessToken.objects.get(token=access_token,
                expires__gt=now(), client=client)
        except AccessToken.DoesNotExist:
            return None
