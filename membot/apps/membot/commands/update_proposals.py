import argparse, os, sys, traceback
import github3
import io
import json
import os
import requests
from operator import itemgetter

SCREENDOOR_CONFIG = {
    'PROJECT_ID': 2480,
    'API_KEY': os.environ['SCREENDOOR_API_KEY'],
    'API_URL_PREFIX': 'https://screendoor.dobt.co/api',
}

GITHUB_CONFIG = {
    'TOKEN': os.environ['GITHUB_TOKEN'],
    'REPO_OWNER': 'opennews',
    'REPO_NAME': 'srccon',
    'DATA_PATH_PROPOSALS': '_data/proposals.yml',
    'DATA_PATH_SESSIONS': '_data/sessions.yml',
    'TARGET_BRANCH': 'gh-pages',
}

SCREENDOOR_RESPONSE_MAP = {
    'title_field_id': 30914,
    'description_field_id': 30915,
    'facilitator_name_id': 30918,
    'facilitator_twitter_id': 30920,
    'needs_cofacilitator': 30921,
    'cofacilitator_name_id': 30924,
    'cofacilitator_twitter_id': 30926,
}

def fetch_from_screendoor():
    '''
    Hit the Screendoor API and fetch proposals for `SCREENDOOR_PROJECT_ID`.
    '''
    data = []

    # compile data from the API, handling paginated responses
    # by checking for 'next' in link header
    def _fetch(url):
        r = requests.get(url)
        data.extend(r.json())

        if 'next' in r.links:
            _fetch(r.links['next']['url'])
    
    # build the first URL to hit    
    API_ENDPOINT = '{0}/projects/{1}/responses?v=0&api_key={2}'.format(SCREENDOOR_CONFIG['API_URL_PREFIX'], SCREENDOOR_CONFIG['PROJECT_ID'], SCREENDOOR_CONFIG['API_KEY'])

    # begin the fetch routine
    _fetch(API_ENDPOINT)

    return data

def transform_data(data):
    '''
    Pares down individual proposal items to just the fields we want to publish.
    '''
    def _transform_response_item(item):
        _responses = item.get('responses', {})

        # map Screendoor form fields to the JSON fields we want
        _transformed = {
            'id': item.get('id', None),
            'submitted_at': item.get('submitted_at', None),
            'title': _responses.get(str(SCREENDOOR_RESPONSE_MAP['title_field_id']), None),
            'description': _responses.get(str(SCREENDOOR_RESPONSE_MAP['description_field_id']), None),
            'facilitator': _responses.get(str(SCREENDOOR_RESPONSE_MAP['facilitator_name_id']), None),
            'facilitator_twitter': _responses.get(str(SCREENDOOR_RESPONSE_MAP['facilitator_twitter_id']), None),
            'cofacilitator': None,
            'cofacilitator_twitter': None,
        }

        # if submitter fills in cofacilitator data but then changes dropdown back to "nope,"
        # we *don't* want the cofacilitator information they filled out
        _needs_cofacilitator = _responses.get(str(SCREENDOOR_RESPONSE_MAP['needs_cofacilitator']), None).get('selected', None) != 'Nope, I\'m all good'
        if _needs_cofacilitator:
            _transformed['cofacilitator'] = _responses.get(str(SCREENDOOR_RESPONSE_MAP['cofacilitator_name_id']), None)
            _transformed['cofacilitator_twitter'] = _responses.get(str(SCREENDOOR_RESPONSE_MAP['cofacilitator_twitter_id']), None)

        # strip empty spaces, and line breaks that Screendoor adds to text fields
        _transformed_item = { key: (value.strip().lstrip('\n\n') if isinstance(value, basestring) else value) for key, value in _transformed.iteritems() }

        return _transformed_item
    
    transformed_data = [_transform_response_item(item) for item in data]
    
    return transformed_data

def sort_data(data, alpha=False):
    '''
    Sort most recent proposals to the top, using `id` key as a shortcut.
    '''
    if alpha:
        sorted_data = sorted(data, key=itemgetter('title'))
    else:
        sorted_data = sorted(data, key=itemgetter('id'), reverse=True)
    
    return sorted_data

def filter_data(data, exclude_label=None, include_label=None, exclude_status=None, include_status=None):
    '''
    Filters out proposal items that aren't intended for publication.
    '''
    
    if exclude_label:
        filtered_data = [item for item in data if not exclude_label in item['labels']]
        
    if include_label:
        filtered_data = [item for item in data if include_label in item['labels']]
        
    if exclude_status:
        filtered_data = [item for item in data if status != item['status']]

    if include_status:
        filtered_data = [item for item in data if include_status == item['status']]

    return filtered_data

def make_json(data, store_locally=False, filename='proposals.json'):
    '''
    Turns data into nice JSON, and optionally stores to a local file.
    '''
    json_out = json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False)
    
    if store_locally:
        with io.open(filename, 'w', encoding='utf8') as outfile:
            outfile.write(unicode(json_out))

    return json_out.encode('utf-8')

def commit_json(data, target_file=GITHUB_CONFIG['DATA_PATH_PROPOSALS']):
    '''
    Uses token to log into GitHub as `ryanpitts`, then gets the appropriate
    repo based on owner/name defined in GITHUB_CONFIG.
    
    Creates proposal data file if it does not exist in the repo, otherwise
    updates existing data file.
    '''
    
    # authenticate with GitHub
    gh = github3.login(token=GITHUB_CONFIG['TOKEN'])
    
    # get the right repo
    repo = gh.repository(GITHUB_CONFIG['REPO_OWNER'], GITHUB_CONFIG['REPO_NAME'])
    
    # check to see whether data file exists
    contents = repo.file_contents(
        path=target_file,
        ref=GITHUB_CONFIG['TARGET_BRANCH']
    )

    if not contents:
        # create file that doesn't exist
        repo.create_file(
            path=target_file,
            message='adding session data',
            content=data,
            branch=GITHUB_CONFIG['TARGET_BRANCH']
        )
    else:
        # update existing file
        contents.update(
            message='updating session data',
            content=data,
            branch=GITHUB_CONFIG['TARGET_BRANCH']
        )

def update_proposals():
    data = fetch_from_screendoor()
    #print 'Fetched the data ...'

    # PROPOSALS
    data = filter_data(data, exclude_label='Hidden')
    # SESSIONS
    #data = filter_data(data, include_status='Confirmed -- accepted session')

    data = transform_data(data)
    # PROPOSALS
    data = sort_data(data)
    # SESSIONS
    #data = sort_data(data, alpha=True)
    #print 'Prepped the data ...'

    # PROPOSALS
    proposal_json = make_json(data, store_locally=False, filename='proposals.json')
    # SESSIONS
    #session_json = make_json(data, store_locally=False, filename='sessions.json')
    #print 'Made the local json!'

    # PROPOSALS
    commit_json(proposal_json)
    # SESSIONS
    #commit_json(session_json, target_file=GITHUB_CONFIG['DATA_PATH_SESSIONS'])
    #print 'SENT THE DATA TO GITHUB!'


if __name__ == "__main__":
    try:
        update_proposals()
    except Exception, e:
        sys.stderr.write('\n')
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write('\n')
        sys.exit(1)
