import os
import requests
import string

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .models import Memory

SLACK_TOKEN = os.environ['SLACK_TOKEN']
INBOUND_SLACK_TOKEN = os.environ['INBOUND_SLACK_TOKEN']
BOT_NAME = 'membot'
KNOWN_COMMANDS = ['show',]

def homepage(request):
    return HttpResponse('Hello world this is membot')    

class MessageView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(MessageView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        received = request.POST
        auth_token = received.get('token', None)
        
        # make sure message is coming from an authorized place
        if auth_token != INBOUND_SLACK_TOKEN:
            return HttpResponseForbidden()
        
        # send the message into Slack
        message = received.get('message', '')
        channel = received.get('channel', 'general')
        endpoint = 'https://opennews.slack.com/services/hooks/slackbot?token={0}&channel=%23{1}'.format(INBOUND_SLACK_TOKEN, channel)
        r = requests.post(endpoint, data=message)                    
        
        return JsonResponse({'text': 'message sent'})

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
            self.set_response('Yes <@{0}>?'.format(command['person']))

        # otherwise take action
        else:
            if 'special' in command:
                action = command['special']

                if action not in KNOWN_COMMANDS:
                    self.set_response('\'{0}\' sounds like a special command, <@{1}>, but I haven\'t learned that one yet :('.format(command['special'], command['person']))
                
                if action == 'show':
                    memories = []
                    #TODO: handle `since` option

                    memories = Memory.objects.filter(is_active=True, category__in=command['categories']).distinct()
                    
                    if memories:
                        intro = 'Here\'s what I remember about {0}:\n'.format(' '.join(command['categories']))
                        report = []

                        for memory in memories:
                            report.append('- On {0}, <@{1}> said: {2}'.format(memory.created.strftime('%B %d'), memory.person, memory.text))

                        self.set_response(intro + '```' + '\n'.join(report) + '```')
                    else:
                        self.set_response('Sorry, I don\'t remember anything like that!')

            # we have a memory to log, so do it for each defined category
            else:
                for category in command['categories']:
                    kwargs = {
                        'text': command['text'],
                        'person': command['person'],
                        'category': category,
                    }
                    memory = Memory(**kwargs)
                    memory.save()
                
                self.set_response('Got it, <@{0}>!'.format(command['person']))

        return JsonResponse(self.response)

    def set_response(self, text):
        self.response['text'] = text
        
    def parse_command(self, received):
        # split the command text for cleaning
        tokens = received.get('text', '').split(' ')
        
        # we don't need the bot name, and using `startswith`
        # catches most natural language punctuation
        if tokens[0].lower().startswith(BOT_NAME):
            del tokens[0]

        # just in case we had punctuation after the trigger name
        if tokens and tokens[0].lower() in list(string.punctuation):
            del tokens[0]

        # collect the hashtags
        categories = []
        for token in tokens:
            if token.startswith('#'):
                categories.append(token.lower().rstrip(string.punctuation))
                
        # give ourselves a default category if nothing else
        if not categories:
            categories = ['#general']

        # begin the command dict
        command = {
            'person': received.get('user_name', None),
            'categories': categories,
        }

        # see if we have a special command
        if tokens and tokens[0].lower() in ['please', 'plz']:
            del tokens[0]

            # take the next word for our special command
            if tokens:
                command.update({
                    'special': tokens.pop(0),
                })

        # finally we have our text
        command.update({
            'text': ' '.join(tokens),
        })

        return command