import os

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .models import Memory

SLACK_TOKEN = os.environ['SLACK_TOKEN']
BOT_NAME = 'membot'

def homepage(request):
    return HttpResponse('Hello world this is membot')    

class CommandView(View):
    response = {'text': ''}
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(CommandView, self).dispatch(*args, **kwargs)
        
    def post(self, request, *args, **kwargs):
        received = request.POST
        auth_token = received.get('token', None)
        
        # make sure command is coming from the right place
        if auth_token != SLACK_TOKEN:
            return HttpResponseForbidden()

        # collect our command params
        command = self.parse_command(received)
        
        # if we don't actually have a command ...
        if not command['text']:
            self.set_response('Yes <@%s>?' % (command['user_name']))

        # otherwise take action
        else:
            # TODO
            if 'special' in command:
                self.set_response('\'%s\' sounds like a special command, <@%s>, but I haven\'t learned that one yet :(' % (command['special'], command['user_name']))

            # we have a memory to log, so do it for each defined category
            else:
                for category in categories:
                    memory = Memory({
                        'text': command['text'],
                        'person': command['person'],
                        'category': category,
                    })
                    memory.save()
                
                self.set_response('Got it, <@%s>!' % (command['user_name']))

        return JsonResponse(self.response)

    def set_response(text):
        self.response['text'] = text
        
    def parse_command(received):
        # split the command text for cleaning
        tokens = received.get('text', '').split(' ')
        
        # we don't need the bot name
        if tokens[0].lower() == BOT_NAME:
            del tokens[0]

        # just in case we had punctuation after the trigger name
        if tokens[0].lower() in [',', ':', '!', '?']:
            del tokens[0]

        # collect the hashtags
        categories = []
        for token in tokens:
            if token.startswith('#'):
                categories.append(token)
                
        # give ourselves a default category if nothing else
        if not categories:
            categories = ['#general']

        # begin the command dict
        command = {
            'user_name': received.get('user_name', None),
            'categories': categories,
        }

        # see if we have a special command
        if tokens[0].lower() in ['please', 'plz']:
            del tokens[0]

            # take the next word for our special command
            command.update({
                'special': tokens.pop(0),
            })

        # finally we have our text
        command.update({
            'text': ' '.join(tokens),
        })

        return command