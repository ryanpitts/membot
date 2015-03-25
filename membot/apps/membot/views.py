import os
import random
import re
import requests
import string

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .commands import update_proposals, build_opennews_site
from .models import Memory

SLACK_TOKEN = os.environ['SLACK_TOKEN']
ALT_SLACK_TOKEN = os.environ['ALT_SLACK_TOKEN']
INBOUND_SLACK_TOKEN = os.environ['INBOUND_SLACK_TOKEN']
KNOWN_COMMANDS = {
    'membot': ['show',],
    'hey bmo': ['publish proposals', 'build opennews'],
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

class MembotCommandView(View):
    response = {'text': ''}
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(MembotCommandView, self).dispatch(*args, **kwargs)
        
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

                if action not in KNOWN_COMMANDS['membot']:
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
        if tokens[0].lower().startswith('membot'):
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


class RevisedCommandView(View):
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

        if action == 'publish proposals':
            try:
                update_proposals()
                affirmative = self.random_affirmative(self.command['person'])
                self.set_response('{0} I just added the latest data to http://srccon.org/sessions/proposals.'.format(affirmative))
            except:
                self.set_response('Oh no, something went wrong, {0}.'.format(self.command['person']))
            return JsonResponse(self.response)

        if action == 'build opennews':
            success = build_opennews_site()
            if success:
                affirmative = self.random_affirmative(self.command['person'])
                self.set_response('{0} I just rebuilt http://opennews.org.'.format(affirmative))
            else:
                self.set_response('Oh no, I asked Jenkins but something went wrong, {0}.'.format(self.command['person']))
            return JsonResponse(self.response)

        # we're only here if everything failed for some reason
        self.set_response('Whoa, that\'s weird. Not sure what just happened.')
        return JsonResponse(self.response)
        
    def set_response(self, text):
        self.response['text'] = text
        
    def random_affirmative(self, person):
        possibles = ['I have your back, {0}.', 'I am on it, {0}.', 'I am red hot like pizza supper, {0}.', 'BMO Chop! If this were a real attack, {0}, you\'d be dead. But', 'I used the combo move, {0}!']
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

