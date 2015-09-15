import argparse, os, sys, traceback
import github3
import io
import json
import os
import requests

GITHUB_CONFIG = {
    'TOKEN': os.environ['GITHUB_TOKEN'],
}

GITHUB_REPOS = [
        'https://github.com/NYTimes/pourover',
        'https://github.com/NYTimes/tamper',
        'https://github.com/nprapps/pym.js',
        'https://github.com/propublica/landline',
        'https://github.com/veltman/fourscore',
        'https://github.com/california-civic-data-coalition/django-calaccess-raw-data',
        'https://github.com/california-civic-data-coalition/django-calaccess-campaign-browser',
        'https://github.com/veltman/wherewolf',
        'https://github.com/washingtonpost/whippersnapper',
        'https://github.com/MinnPost/election-night-api',
        'https://github.com/openelections/clarify',
        'https://github.com/seattletimes/component-sort-table',
        'https://github.com/seattletimes/component-simple-graph',
        'https://github.com/newsdev/driveshaft',
        'https://github.com/INN/Largo',
        'https://github.com/texastribune/donation-builder',
        'https://github.com/associatedpress/geomancer',
        'https://github.com/debrouwere/google-analytics',
        'https://github.com/debrouwere/facebook-insights',
        'https://github.com/debrouwere/social-shares',
        'https://github.com/flatsheet/flatsheet',
        'https://github.com/voxmedia/autotune/',
        'https://github.com/nprapps/lunchbox',
        'https://github.com/ftzeng/broca',
        'https://github.com/julia67/data-viz-for-all'
]

def get_stats():
    stats = {
        'projects': 0,
        'contributors': 0,
        'forks': 0,
        'stars': 0,
    }
    
    # authenticate with GitHub
    gh = github3.login(token=GITHUB_CONFIG['TOKEN'])
    
    for url in GITHUB_REPOS:
        url_bits = url.split('/')
        repo_name = url_bits[-1]
        repo_owner = url_bits[-2]

        r = requests.get('https://api.github.com/repos/{0}/{1}?access_token={2}'.format(repo_owner, repo_name, GITHUB_CONFIG['TOKEN']))
        data = r.json()
        
        if data:
            stats['projects'] += 1
            
            if 'forks' in data: stats['forks'] += data['forks']
            if 'stargazers_count' in data: stats['stars'] += data['stargazers_count']
        
            if 'contributors_url' in data:
                r = requests.get('{0}?access_token={1}'.format(data['contributors_url'], GITHUB_CONFIG['TOKEN']))
                stats['contributors'] += len(r.json())
    
    return stats


if __name__ == "__main__":
    try:
        get_stats()
    except Exception, e:
        sys.stderr.write('\n')
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write('\n')
        sys.exit(1)
