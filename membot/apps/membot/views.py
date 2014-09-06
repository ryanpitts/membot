import os

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

SLACK_TOKEN = os.environ['SLACK_TOKEN']

def homepage(request):
    return HttpResponse('Hello world this is membot')    

class CommandView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(CommandView, self).dispatch(*args, **kwargs)
        
    def post(self, request, *args, **kwargs):
        received = request.POST
        token = received.get('token', None)
        user_name = received.get('user_name', None)
        text = received.get('text', None)
        
        # make sure command is coming from the right place
        if token != SLACK_TOKEN:
            return HttpResponseForbidden
        
        response = {
            'text': 'Membot is here, <@%s>! I heard you say \'%s\'' % (user_name, text)
        }

        return JsonResponse(response)
