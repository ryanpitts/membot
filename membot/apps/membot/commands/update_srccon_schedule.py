import os, sys, traceback
import github3
import gspread
import io
import json
import logging
from logging.config import dictConfig


GITHUB_CONFIG = {
    'TOKEN': os.environ['GITHUB_TOKEN'],
    'REPO_OWNER': 'opennews',
    'REPO_NAME': 'srccon-2022',
    'TARGET_FILE': 'schedule/sessions.json',
    'TARGET_BRANCHES': ['main','staging',],# choose one or more branches
}

GITHUB_SRCCON_YAML_CONFIG = {
    'TOKEN': os.environ['GITHUB_TOKEN'],
    'REPO_OWNER': 'opennews',
    'REPO_NAME': 'srccon-2022',
    'TARGET_FILE': '_data/schedule.yaml',
    'TARGET_BRANCHES': ['main',],
}

GOOGLE_API_CREDENTIALS = {
    "type": "service_account",
    "private_key": os.environ["GOOGLE_API_PRIVATE_KEY"].encode().decode('unicode_escape'),
    "client_email": os.environ["GOOGLE_API_CLIENT_EMAIL"],
    "token_uri": "https://oauth2.googleapis.com/token",
}

# the unique ID of the spreadsheet with your data can be stored
# as an environment variable or simply added here as a string
GOOGLE_SPREADSHEET_KEY = '1k8iPZAmWFU0fzSkdS6u1jWU-OwlxELIgKNRdGaIpRKQ'
#GOOGLE_SPREADSHEET_KEY = os.environ['GOOGLE_SPREADSHEET_KEY']

# pull data from a named worksheet, or leave blank to assume first worksheet
GOOGLE_SPREADSHEET_SHEETNAME = 'schedule data'

# if data is spread across multiple worksheets, set to True
FETCH_MULTIPLE_WORKSHEETS = False

# if fetching multiple worksheets, name sheets to skip here
# EXAMPLE: WORKSHEETS_TO_SKIP = ['Sheet1', 'Sheet4',]
WORKSHEETS_TO_SKIP = []

# set to True to store local version of JSON
MAKE_LOCAL_JSON = False

# set to False for dry runs
COMMIT_JSON_TO_GITHUB = True

# TODO: Add method for storing JSON output in S3 bucket
# S3_CONFIG = {}
# SEND_JSON_TO_S3 = False

def authenticate_with_google():
    '''
    Connect to Google Spreadsheet with gspread library.
    '''
    google_api_conn = gspread.service_account_from_dict(GOOGLE_API_CREDENTIALS)
    
    return google_api_conn
    
def open_google_spreadsheet():
    '''
    Authenticate and return spreadsheet by `GOOGLE_SPREADSHEET_KEY`.
    '''
    google_api_conn = authenticate_with_google()
    spreadsheet = google_api_conn.open_by_key(GOOGLE_SPREADSHEET_KEY)
    
    return spreadsheet

def fetch_data(multiple_sheets=False, worksheets_to_skip=[]):
    spreadsheet = open_google_spreadsheet()

    if not multiple_sheets:
        # Return data from named worksheet if specified ...
        if GOOGLE_SPREADSHEET_SHEETNAME:
            worksheet = spreadsheet.worksheet(GOOGLE_SPREADSHEET_SHEETNAME)
        # .. otherwise return data from the first worksheet
        else:
            worksheet = spreadsheet.get_worksheet(0)

        data = worksheet.get_all_records(empty2zero=False)

    else:
        # Return data from all worksheets in Google spreadsheet, optionally
        # skipping sheets identified by title in `WORKSHEETS_TO_SKIP`
        data = []
        worksheet_list = [
            sheet for sheet in spreadsheet.worksheets() if sheet.title not in WORKSHEETS_TO_SKIP
        ]

        for worksheet in worksheet_list:
            worksheet.title
            data.extend(worksheet.get_all_records(empty2zero=False))

    return data

def transform_data(data):
    '''
    Transforms data and filters/validates individual spreadsheet rows
    for fields we want in the JSON output. Currently, this:
    
    * ensures that all variables going into the JSON are strings
    
    Additional filters should be added to _transform_response_item.
    '''
    def _transform_response_item(item, skip=False):
        # make sure vars are strings
        _transformed_item = {k: v for k, v in item.items() if k}
        
        # EXAMPLE: get rid of data from column `rowNumber`
        # if 'rowNumber' in _transformed_item:
        #     del _transformed_item['rowNumber']
        
        # EXAMPLE: rename spreadsheet column `name` into JSON key `title`
        # if 'name' in _transformed_item:
        #     _transformed_item['title'] = _transformed_item.pop('name', '')
        
        # EXAMPLE: use `skip` flag to ignore rows without valid id
        # if 'id' in _transformed_item:
        #     try:
        #         int(_transformed_item['id'])
        #     except:
        #         skip = True
        
        # if we've triggered the skip flag anywhere, drop this record
        if skip:
            _transformed_item = None
            
        return _transformed_item
    
    # pass spreadsheet rows through the transformer
    transformed_data = [_transform_response_item(item) for item in data]
    transformed_data = [item for item in transformed_data if item]
    
    return transformed_data

def make_json(data, store_locally=False, filename=GITHUB_CONFIG['TARGET_FILE']):
    '''
    Turns data into nice JSON, and optionally stores to a local file.
    '''
    json_out = json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False)
    
    if store_locally:
        with io.open(filename, 'w', encoding='utf8') as outfile:
            outfile.write(json_out)

    return json_out.encode('utf-8')

def commit_json(data, target_config=GITHUB_CONFIG, commit=COMMIT_JSON_TO_GITHUB):
    '''
    Uses token to log into GitHub, then gets the appropriate repo based
    on owner/name defined in GITHUB_CONFIG.
    
    Creates data file if it does not exist in the repo, otherwise updates
    existing data file.
    
    If `COMMIT_JSON_TO_GITHUB` is False, this will operate in "dry run" mode,
    authenticating against GitHub but not changing any files.
    '''
    
    # authenticate with GitHub
    gh = github3.login(token=target_config['TOKEN'])
    
    # get the right repo
    repo = gh.repository(target_config['REPO_OWNER'], target_config['REPO_NAME'])
    
    for branch in target_config['TARGET_BRANCHES']:
        # check to see whether data file exists
        try:
            contents = repo.file_contents(
                path=target_config['TARGET_FILE'],
                ref=branch
            )
        except:
            contents = None

        if commit:
            if not contents:
                # create file that doesn't exist
                repo.create_file(
                    path=target_config['TARGET_FILE'],
                    message='adding session data for schedule',
                    content=data,
                    branch=branch
                )
                logger.info('Created new data file in repo')
            else:
                # if data has changed, update existing file
                if data.decode('utf-8') == contents.decoded.decode('utf-8'):
                    logger.info('Data has not changed, no commit created')
                else:
                    contents.update(
                        message='updating schedule data',
                        content=data,
                        branch=branch
                    )
                    logger.info('Data updated, new commit to repo')
                

def update_srccon_schedule():
    data = fetch_data(multiple_sheets=FETCH_MULTIPLE_WORKSHEETS, worksheets_to_skip=WORKSHEETS_TO_SKIP)
    #print 'Fetched the data ...'

    data = transform_data(data)
    #print 'Prepped the data ...'

    json_data = make_json(data, store_locally=MAKE_LOCAL_JSON)
    #print 'Made some JSON!'

    #commit_json(json_data, target_config=GITHUB_SRCCON_YAML_CONFIG)
    #print 'SENT THE DATA TO GITHUB!'

    commit_json(json_data)
    #print 'Sent the data to GitHub!'


'''
Set up logging.
'''
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'log.txt',
            'formatter': 'verbose'
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'schedule_loader': {
            'handlers':['file','console'],
            'propagate': False,
            'level':'DEBUG',
        }
    }
}
dictConfig(LOGGING)
logger = logging.getLogger('schedule_loader')


if __name__ == "__main__":
    try:
        update_srccon_schedule()
    except Exception:
        sys.stderr.write('\n')
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write('\n')
        sys.exit(1)
