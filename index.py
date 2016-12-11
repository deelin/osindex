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


OUT_FILE = os.path.join('/', 'Users', 'dlin', "index-" +
                        datetime.now().isoformat().split('T')[0] + '.csv')
def index_kw(kw_file, out_file=OUT_FILE):
    SEPARATOR = "|"
    headers = {"Accept": "application/vnd.github.v3.text-match+json"}

    kws = format_kw(kw_file)
    sorted_kws = sort([kw[0] for kw in kws])
    with open('/tmp/sorted.txt', 'w') as f:
        f.write('\n'.join(sorted_kws))
    with open(out_file, 'a') as f:
        for pair in kws:
            time.sleep(60)

            fields = []
            name = pair[0]
            corrected_name = correct_keys(pair[0])
            print "Starting for %s which was corrected to %s" % (name, corrected_name)
            fields = [name]
            if name in sorted_kws:
                fields.append(str(len(sorted_kws) - sorted_kws.index(name) + 1))
            else:
                fields.append('???')

            indeed = "http://www.indeed.com/jobs?q=%s&l=" % corrected_name
            simply_hired = "http://www.simplyhired.com/search?q=%s" % corrected_name
            stack_overflow = "http://stackoverflow.com/search?q=%s" % name

            # INDEED
            indeed_resp = requests.get(indeed)
            indeed_total_index = indeed_resp.text.find('<div id="searchCount')
            if indeed_total_index > 0:
                indeed_total_str = indeed_resp.text[indeed_total_index:indeed_total_index + 100]
                indeed_rx = re.search('Jobs [0-9,]+ to [0-9,]+ of ([0-9,]+)', indeed_total_str)
                indeed_job_count = int(''.join(indeed_rx.groups()[0].split(',')))
                fields.append(indeed_job_count)
            else:
                fields.append(0)

            # SIMPLYHIRED
            sh_resp = requests.get(simply_hired)
            sh_total_index = sh_resp.text.find('<div style="float:right">Showing ')
            if sh_total_index > 0:
                sh_total_str = sh_resp.text[sh_total_index:sh_total_index + 100]
                sh_rx = re.search('[0-9,-]+ of ([0-9,]+)', sh_total_str)
                sh_job_count = int(''.join(sh_rx.groups()[0].split(',')))
                fields.append(sh_job_count)
            else:
                fields.append(0)

            # STACKOVERFLOW
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
                fields.append(so_question_count)
            else:
                fields.append(0)

            if pair[1]:
                # Github available, check github for stars etc.
                url = "https://api.github.com/search/repositories?q=user:%s+%s&stars:>1&sort=stars&order=desc" % pair[
                    1:]
                x = requests.get(url, headers=headers)
                page = json.loads(x.text)
                if 'items' not in page:
                    break
                items = page['items']
                if len(items) > 0:
                    item = items[0]
                    forks = item['forks_count']
                    fields.append(forks)
                    stars = item['stargazers_count']
                    fields.append(stars)
                    watchers = item['watchers_count']
                    fields.append(watchers)
                    url = item['html_url']
                    fields.append(url)

            line = SEPARATOR.join([unicode(x) for x in fields]).encode('utf-8')
            print "Writing " + line
            f.write(line)
            f.write('\n')

