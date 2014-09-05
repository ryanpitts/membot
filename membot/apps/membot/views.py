import os

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.generic import View

SLACK_TOKEN = os.environ['SLACK_TOKEN']
SLACK_TEAM_ID = os.environ['SLACK_TEAM_ID']

def homepage(request):
    return HttpResponse('Hello world this is membot')    

class CommandView(View):
    def post(self, request, *args, **kwargs):
        received = request.POST
        
        # make sure command is coming from the right place
        if received.token != SLACK_TOKEN or received.team_id != SLACK_TEAM_ID:
            return HttpResponseForbidden

        response = {
            'text': 'Membot is here, <@%s>! I heard you say \'%s\'' % (received.user_name, received.text)
        }

        return JsonResponse(response)
