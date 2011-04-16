from commis import conf
from commis.clients.forms import ClientForm
from commis.clients.models import Client
from commis.exceptions import ChefAPIError
from commis.generic_views import CommisAPIView, api, CommisView

class ClientAPIView(CommisAPIView):
    model = Client

    @api('POST')
    def create(self, request):
        if not (request.client.admin or request.client.name == conf.COMMIS_VALIDATOR_NAME):
            raise ChefAPIError(403, 'You are not allowed to take this action')
        super(ClientAPIView, self).create(request)


class ClientView(CommisView):
    model = Client
    form = ClientForm
