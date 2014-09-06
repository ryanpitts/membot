import os

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

SLACK_TOKEN = os.environ['SLACK_TOKEN']

def homepage(request):
    return HttpResponse('Hello world this is membot')    

@csrf_exempt
class CommandView(View):
    def post(self, request, *args, **kwargs):
        received = request.POST
        token = received.get('token', None)
        user_name = received.get('user_name', None)
        text = received.get('text', None)
        
        # make sure command is coming from the right place
        #if token != SLACK_TOKEN:
        #    return HttpResponseForbidden
        
        response = {
            'text': 'Membot is here, <@%s>! I heard you say \'%s\' with token \'%s\', expecting token \'%s\'' % (user_name, text, token, SLACK_TOKEN)
        }

        return JsonResponse(response)
