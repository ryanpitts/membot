import os
import requests

JENKINS_CONFIG = {
    'JENKINS_OPENNEWS_BUILD_TOKEN': os.environ['JENKINS_OPENNEWS_BUILD_TOKEN'],
    'JENKINS_URL': os.environ['JENKINS_URL'],
    'JENKINS_JOB_URL': '/view/PROD/job/PRODPUSH-opennews/build',
}

def build_opennews_site():
    JENKINS_TRIGGER_URL = '{0}{1}?token={2}'.format(JENKINS_CONFIG['JENKINS_URL'], JENKINS_CONFIG['JENKINS_JOB_URL'], JENKINS_CONFIG['JENKINS_OPENNEWS_BUILD_TOKEN'])
    
    r = requests.post(JENKINS_TRIGGER_URL)
    if r.status_code != 201:
        return False
    return True

if __name__ == "__main__":
    build_opennews_site()
