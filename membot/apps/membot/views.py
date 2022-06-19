import os
import random
import re
import requests
import string

import arrow

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .commands import update_srccon_schedule

SLACK_TOKEN = os.environ['SLACK_TOKEN']
ALT_SLACK_TOKEN = os.environ['ALT_SLACK_TOKEN']
INBOUND_SLACK_TOKEN = os.environ['INBOUND_SLACK_TOKEN']
KNOWN_COMMANDS = {
    'hey bmo': ['build srccon schedule',],
}
BOT_NAMES = KNOWN_COMMANDS.keys()

def hello(request):
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
    received = ''

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(RevisedCommandView, self).dispatch(*args, **kwargs)

    def verify_auth_token(self):
        '''
        make sure command is coming from the right place
        '''
        self.auth_token = self.received.get('token', None)

        if self.auth_token != ALT_SLACK_TOKEN:
            return False
        return True

    def post(self, request, *args, **kwargs):
        self.received = request.POST

        if not self.verify_auth_token():
            return HttpResponseForbidden()

        self.parse_command()
        self.parse_command_person()

        # if we don't actually have a command ...
        if not self.command['text']:
            self.set_response('Hey {0}, what\'s up?'.format(self.command['person']))
            return JsonResponse(self.response)

        # otherwise take action
        action = self.command['action']

        if not action:
            suffix = ''
            if len(KNOWN_COMMANDS[self.command['botname']]) < 2:
                suffix = ' (Yeah, I don\'t get to do a lot yet.)' 
            self.set_response('Hmmm, I\'m not sure how to do that, {0}. Here\'s what I\'m authorized to do: {1}.{2}'.format(self.command['person'], (', ').join(KNOWN_COMMANDS[self.command['botname']]), suffix))
            return JsonResponse(self.response)

        if action == 'build srccon schedule':
            try:
                update_srccon_schedule()
                affirmative = self.random_affirmative(self.command['person'])
                self.set_response('{0} I just sent the data from our schedule spreadsheet into https://2021.srccon.org/schedule.'.format(affirmative))
            except:
                self.set_response('Oh no, something went wrong, {0}.'.format(self.command['person']))
            return JsonResponse(self.response)

        # we're only here if everything failed for some reason
        self.set_response('Whoa, that\'s weird. Not sure what just happened.')
        return JsonResponse(self.response)
        
    def set_response(self, text):
        self.response['text'] = text
        
    def random_affirmative(self, person):
        possibles = ['I have your back, {0}.', 'I am red hot like pizza supper, {0}.', 'BMO Chop! If this were a real attack, {0}, you\'d be dead. But', 'I used the combo move, {0}!']
        return random.choice(possibles).format(person)

    def parse_command_person(self):
        if self.command['person'] == '<@ryanpitts>' and self.command['botname'] == 'hey cody':
            self.command['person'] = 'Dad'
        
    def parse_command(self):
        self.raw_command = self.received.get('text', '')
        self.command = {
            'person': '<@' + self.received.get('user_name', 'channel') + '>',
            'botname': '',
            'action': '',
            'text': '',
        }

        # we don't need the bot name, and using `startswith`
        # catches most natural language punctuation
        for name in BOT_NAMES:
            if self.raw_command.lower().startswith(name.lower()):
                self.command['botname'] = name
                botmatch = re.compile(name, re.IGNORECASE)
                self.command['text'] = botmatch.sub('', self.raw_command, 1)

        # if we have an empty string at this point, bail
        if not self.command['text']:
            return
            
        # just in case we had punctuation after the trigger name
        if self.command['text'][0] in list(string.punctuation):
            self.command['text'] = self.command['text'][1:]

        # split the command text into tokens
        tokens = self.command['text'].strip().split(' ')
        exclude = set(string.punctuation)
        tokens = [''.join(ch for ch in token if ch not in exclude) for token in tokens]

        for command in KNOWN_COMMANDS[self.command['botname']]:
            command_words = command.split(' ')
            if set(command_words).issubset(set(tokens)):
                self.command['action'] = command
                break

