import argparse, os, sys, traceback
import github3
import gspread
import io
import json
import os
import requests

from oauth2client.client import SignedJwtAssertionCredentials

GITHUB_CONFIG = {
    'TOKEN': os.environ['GITHUB_TOKEN'],
    'REPO_OWNER': 'ryanpitts',
    'REPO_NAME': 'mozfest-test-schedule',
    'DATA_PATH_SESSIONS': 'sessions.json',
    'TARGET_BRANCH': 'gh-pages',
}

GOOGLE_API_CONFIG = {
    'CLIENT_EMAIL': os.environ['GOOGLE_API_CLIENT_EMAIL'],
    'PRIVATE_KEY': os.environ['GOOGLE_API_PRIVATE_KEY'].decode('unicode_escape'),
    'SCOPE': ['https://spreadsheets.google.com/feeds']
}
GOOGLE_SPREADSHEET_KEY = '1rSekJIdPkhlu9I4ousIEEb4RGeJd_k4c7HWxdwfxC7k'
GOOGLE_SPREADSHEET_WORKSHEET = 'schedule data'

def fetch_from_spreadsheet():
    '''
    Connect to Google Spreadsheet with gspread library and fetch schedule data.
    '''
    credentials = SignedJwtAssertionCredentials(
        GOOGLE_API_CONFIG['CLIENT_EMAIL'], GOOGLE_API_CONFIG['PRIVATE_KEY'], GOOGLE_API_CONFIG['SCOPE']
    )
    google_api_conn = gspread.authorize(credentials)

    spreadsheet = google_api_conn.open_by_key(GOOGLE_SPREADSHEET_KEY)
    datasheet = spreadsheet.worksheet(GOOGLE_SPREADSHEET_WORKSHEET)

    data = datasheet.get_all_records(empty2zero=False)

    return data

def transform_data(data):
    '''
    Transforms data and filters individual schedule items for fields we want
    to publish. Currently, this:
    
    * ensures that all variables going into the JSON are strings
    '''
    def _transform_response_item(item):
        _transformed_item = {k: unicode(v) for k, v in item.iteritems()}
        return _transformed_item
    
    transformed_data = [_transform_response_item(item) for item in data]
    
    return transformed_data

def make_json(data, store_locally=False, filename=GITHUB_CONFIG['DATA_PATH_SESSIONS']):
    '''
    Turns data into nice JSON, and optionally stores to a local file.
    '''
    json_out = json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False)
    
    if store_locally:
        with io.open(filename, 'w', encoding='utf8') as outfile:
            outfile.write(unicode(json_out))

    return json_out.encode('utf-8')

def commit_json(data, target_config=GITHUB_CONFIG):
    '''
    Uses token to log into GitHub as `ryanpitts`, then gets the appropriate
    repo based on owner/name defined in GITHUB_CONFIG.
    
    Creates sessions data file if it does not exist in the repo, otherwise
    updates existing data file.
    '''
    
    # authenticate with GitHub
    gh = github3.login(token=target_config['TOKEN'])
    
    # get the right repo
    repo = gh.repository(target_config['REPO_OWNER'], target_config['REPO_NAME'])
    
    # check to see whether data file exists
    contents = repo.file_contents(
        path=target_config['DATA_PATH_SESSIONS'],
        ref=target_config['TARGET_BRANCH']
    )

    if not contents:
        # create file that doesn't exist
        repo.create_file(
            path=target_config['DATA_PATH_SESSIONS'],
            message='adding session data',
            content=data,
            branch=target_config['TARGET_BRANCH']
        )
    else:
        # update existing file
        contents.update(
            message='updating session data',
            content=data,
            branch=GITHUB_CONFIG['TARGET_BRANCH']
        )

def update_srccon_schedule():
    data = fetch_from_spreadsheet()
    #print 'Fetched the data ...'

    data = transform_data(data)
    #print 'Prepped the data ...'

    session_json = make_json(data, store_locally=True)
    #print 'Made the local json!'

    commit_json(session_json)
    #print 'SENT THE DATA TO GITHUB!'


if __name__ == "__main__":
    try:
        update_srccon_schedule()
    except Exception, e:
        sys.stderr.write('\n')
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write('\n')
        sys.exit(1)
