#!/usr/bin/env python
import json
import os
import re
import time
from datetime import datetime

import requests

from sorting import sort, correct_keys


class Getter(object):

    def __init__(self):
        pass

class IndeedGetter(Getter):
    pass

class SimplyHiredGetter(Getter):
    pass

class GithubGetter(Getter):
    pass

class StackOverflowGetter(Getter):
    pass


def format_kw(kw_file):
    kws = []
    with open(kw_file, 'r') as f:
        line = f.readline()
        while line:
            line = line.split(',')
            if len(line) != 2:
                print "AHHHH ERROR!"
                raise Exception
            kw = line[0].strip()
            user = ""
            repo = ""
            line[1] = line[1].strip()
            if line[1]:
                repo = line[1].split('/')
                if len(repo) <= 3:
                    print "AHHHH REPO ERROR!"
                    raise Exception
                user = repo[-2]
                repo = repo[-1]
            kws.append((kw, user, repo))
            line = f.readline()
    return kws


"""
INDEED
"""
def fetch_indeed(search_terms):
    indeed = "http://www.indeed.com/jobs?q=%s" % ' '.join(search_terms)
    indeed_resp = requests.get(indeed)
    indeed_total_index = indeed_resp.text.find('<div id="searchCount')
    if indeed_total_index > 0:
        indeed_total_str = indeed_resp.text[indeed_total_index:indeed_total_index + 100]
        indeed_rx = re.search('Jobs [0-9,]+ to [0-9,]+ of ([0-9,]+)', indeed_total_str)
        indeed_job_count = int(''.join(indeed_rx.groups()[0].split(',')))
        return indeed_job_count
    return 0


"""
SIMPLYHIRED
"""
def fetch_simplyhired(search_terms):
    simply_hired = "http://www.simplyhired.com/search?q=%s" % ' '.join(search_terms)
    sh_resp = requests.get(simply_hired)
    sh_total_index = sh_resp.text.find('<div style="float:right">Showing ')
    if sh_total_index > 0:
        sh_total_str = sh_resp.text[sh_total_index:sh_total_index + 100]
        sh_rx = re.search('[0-9,-]+ of ([0-9,]+)', sh_total_str)
        sh_job_count = int(''.join(sh_rx.groups()[0].split(',')))
        return sh_job_count
    return 0


"""
STACKOVERFLOW
"""
def fetch_stackoverflow(search_terms):
    stack_overflow = "http://stackoverflow.com/search?q=%s" % ' '.join(search_terms)
    so_resp = requests.get(stack_overflow)
    time.sleep(2)
    so_total_index = so_resp.text.find('<p>questions tagged</p>')
    if so_total_index > 0:
        so_total_str = so_resp.text[so_total_index - 50:so_total_index]
        so_rx = re.search('summarycount.*>([0-9,]+)', so_total_str)
    else:
        so_total_index = so_resp.text.find('<span class="results-label">results</span>')
        so_total_str = so_resp.text[so_total_index - 100:so_total_index]
        so_rx = re.search('\r\n\s+([0-9,]+)', so_total_str)
    if so_rx:
        so_question_count = int(''.join(so_rx.groups()[0].split(',')))
        return so_question_count
    return 0


"""
Lookup dictionary for keyword search. Need to add search all keywords and aggregate results
"""
SEARCH_KWS = {
    'Postgres': ['Postgresql'],
    'Elasticsearch': ['elastic search'],
    'mongoDB': ['mongo'],
}


OUT_FILE = os.path.join('/', 'Users', 'dlin', "index-" +
                        datetime.now().isoformat().split('T')[0] + '.csv')
def index_kw(kw_file, out_file=OUT_FILE):
    SEPARATOR = "|"
    headers = {"Accept": "application/vnd.github.v3.text-match+json"}

    kws = format_kw(kw_file)
    #sorted_kws = sort([kw[0] for kw in kws])
    #with open('/tmp/sorted.txt', 'w') as f:
    #    f.write('\n'.join(sorted_kws))
    with open(out_file, 'a') as f:
        for pair in kws:
            time.sleep(60)

            fields = []
            name = pair[0]
            corrected_name = correct_keys(pair[0])
            print "Starting for %s which was corrected to %s" % (name, corrected_name)
            fields = [name]
            #if name in sorted_kws:
            #    fields.append(str(len(sorted_kws) - sorted_kws.index(name) + 1))
            #else:
            #    fields.append('???')

            # Indeed
            fields.append(fetch_indeed([corrected_name]))

            # SimplyHired
            fields.append(fetch_simply_hired([corrected_name]))

            # StackOverflow
            fields.append(fetch_stackoverflow([name]))

            if pair[1]:
                # Github available, check github for stars etc.
                url = "https://api.github.com/repos/%s/%s" % pair[1:]
                x = requests.get(url, headers=headers)
                repo = json.loads(x.text)
                git_fields = ['network_count', 'stargazers_count', 'subscribers_count', 'html_url']
                for field in git_fields:
                    if field not in repo:
                        break
                forks = repo['network_count']
                fields.append(forks)
                stars = repo['stargazers_count']
                fields.append(stars)
                watchers = repo['subscribers_count']
                fields.append(watchers)
                url = repo['html_url']
                fields.append(url)

            line = SEPARATOR.join([unicode(x) for x in fields]).encode('utf-8')
            print "Writing " + line
            f.write(line)
            f.write('\n')

