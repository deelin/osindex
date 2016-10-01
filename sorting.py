#!/usr/bin/env python

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import os
import time

"""
    StackOverflow
X   Jobs Sites
*   Google Trends : Use more specific name and multiply by error factor
    Github
"""

# Should be put in database
BROWSER_STACK_USERNAME = 'dennislin1'
BROWSER_STACK_ACCESS_KEY = 'tbZJb61pJZ2S6BFy8bB4'
BASE_URL = "http://www.google.com/trends/fetchComponent?hl=en-US&q=%s&cid=TIMESERIES_GRAPH_0&export=5&w=500&h=300"
DESIRED_CAP = {'os': 'ANY', 'browser': 'chrome'}
ERROR_FACTOR_MAPPING = {
    'Caffe': ('Deep Learning', ''),
    'Graphite': ('Whisper', ''),
    'Marathon': ('Mesosphere', ''),
    'Travis': ('Continuous Integration', ''),
    'Whisper': ('Database', ''),

    'Chef': ('Server', 'Apache Tomcat'),
    'Puppet': ('Server', 'Apache Tomcat'),
    'Terracotta': ('Server', 'Apache Tomcat'),

    # Apache
    'Apex': ('Apache', 'Mesos'),
    'Cassandra': ('Apache', 'Mesos'),
    'Mesos': ('Apache', 'Mesos'),
    'Tomcat': ('Apache', 'Mesos'),

    # Hashicorp
    'Consul': ('Hashicorp', 'Terraform'),
    'Nomad': ('Hashicorp', 'Terraform'),
    'Packer': ('Hashicorp', 'Terraform'),
    'Serf': ('Hashicorp', 'Terraform'),
    'Terraform': ('Hashicorp', 'Terraform'),
    'Vault': ('Hashicorp', 'Terraform'),

    # InfluxDB
    'Kapacitor': ('InfluxDB', 'Kapacitor'),
    'Chronograf': ('InfluxDB', 'Kapacitor'),
    'Telegraf': ('InfluxDB', 'Kapacitor'),
}


# TODO dennis: throttle these calls
def get_trend_comparison(k1, k2):
    print "Comparing %s and %s" % (k1, k2)
    kws = [k1, k2]

    driver = webdriver.Remote(
        command_executor='http://%s:%s@hub.browserstack.com:80/wd/hub' % (BROWSER_STACK_USERNAME,
                                                                          BROWSER_STACK_ACCESS_KEY),
        desired_capabilities=DESIRED_CAP)
    driver.get(BASE_URL % ','.join(kws))

    time.sleep(2)

    html = driver.page_source
    driver.quit()

    # Fetch "paths" from html. Last value of the series of numbers is the ratio
    paths = []
    while len(paths) != 2:
        if html.find('Not enough search volume to show results.') >= 0:
            return 0
        soup = BeautifulSoup(html, 'html.parser')
        paths = filter(lambda x: x if len(str(x)) > 500 else None, soup.find_all('path'))
        if len(paths) != 2:
            print "FAILED! %s %s" % (k1, k2)

    v1 = 200 - float(paths[0]['d'].split(',')[-1])
    v2 = 200 - float(paths[1]['d'].split(',')[-1])
    print "%s has a value of %f" % (k1, v1)
    print "%s has a value of %f" % (k2, v2)

    return (v1, v2)


def get_error_factor(kw, specifier):
    v1, v2 = get_trend_comparison(kw, specifier + ' ' + kw)
    error_factor = v1 / v2
    print "Error factor between %s and %s is %f" % (kw, specifier+' '+kw, error_factor)


def correct_values(key, value, correction_dict):
    if key in ERROR_FACTOR_MAPPING:
        error_factor = correction_dict[ERROR_FACTOR_MAPPING[key]]
        if error_factor:
            return value * error_factor
    return value


def correct_keys(key, correction_dict):
    # Make sure that each key shouldn't be compared as something else
    # Ex: Caffe should be compared as Caffe Deep Learning
    if key in ERROR_FACTOR_MAPPING:
        tup = ERROR_FACTOR_MAPPING[key]
        if not tup[1]:
            return key + " " + tup[0]
    return key



def compare(k1, k2, correction_dict={}):
    k1 = correct_keys(k1, correction_dict)
    k2 = correct_keys(k2, correction_dict)
    v1, v2 = get_trend_comparison(k1, k2)
    v1 = correct_values(k1, v1, correction_dict)
    v2 = correct_values(k2, v2, correction_dict)
    if v1 < v2:
        return -1
    if v1 == v2:
        return 0
    return 1


def scale_score(k1, k2, score, correction_dict):
    """
    Takes a score and scales it down
    """
    v1, v2 = get_trend_comparison(k1, k2)
    v1 = correct_values(k1, v1, correction_dict)
    v2 = correct_values(k2, v2, correction_dict)
    return score * v2 / v1


"""
DEPRECATED
"""
# def get_error_factor(kw, specifier):
#     """
#     Returns a float which can be used to multiply the more specific of two keywords
#     Example:
#         - HBase and Apache HBase
#         get_error_factor('hbase', 'apache') --> 0.01824
#     Multiply # "apache _____" by error factor to get "_____" search frequency
#
#     NOTE: Use very specific kw args in order to properly compare the ratio between
#     including the specifier and not including it
#     """
#     kws = [kw, specifier + " " + kw]
#     paths = []
#     while len(paths) != 2:
#         time.sleep(30)
#         html = get_trends(kws)
#         if html.find('Not enough search volume to show results.') >= 0:
#             return 0
#         soup = BeautifulSoup(html, 'html.parser')
#         paths = filter(lambda x: x if len(str(x)) > 500 else None, soup.find_all('path'))
#         if len(paths) != 2:
#             print "FAILED! %s %s" % (kw, kws[1])
#     v1 = 200 - float(paths[0]['d'].split(',')[-1])
#     v2 = 200 - float(paths[1]['d'].split(',')[-1])
#     return v1/v2


def merge_sort(seq, correction_dict={}):
    """
    Accepts an array. Utilizes merge sort to sort in place, return
    a sorted sequence
    """
    if len(seq) == 1:
        return seq
    else:
        mid = len(seq)/2
        left = merge_sort(seq[:mid], correction_dict)
        right = merge_sort(seq[mid:], correction_dict)

        i, j, k = 0, 0, 0

        while i < len(left) and j < len(right):
            if compare(left[i], right[j], correction_dict) <= 0:
                seq[k] = left[i]
                i += 1
                k += 1
            else:
                seq[k] = right[j]
                j += 1
                k += 1

        remaining = left if i < j else right
        r = i if remaining == left else j

        while r < len(remaining):
            seq[k] = remaining[r]
            r += 1
            k += 1

        return seq


def generate_error_dict():
    error_dict = {}
    for key in ERROR_FACTOR_MAPPING:
        tup = ERROR_FACTOR_MAPPING[key]
        specifier, base_kw = ERROR_FACTOR_MAPPING[key]
        if base_kw:
            if tup not in error_dict:
                error_dict[tup] = get_error_factor(base_kw, specifier)
        else:
            error_dict[tup] = 1
    return error_dict


def sort(kws):
    correction_dict = generate_error_dict()
    sorted = merge_sort(kws, correction_dict)
    with open('x_sorted.txt', 'a') as f:
        for kw in sorted:
            f.write(kw)
            f.write('\n')
    return sorted


SORTED_FILE = os.path.join('/', 'Users', 'dlin', 'code', 'osindex', 'sorted.txt')
def scoring(sorted_file=SORTED_FILE):
    correction_dict = generate_error_dict()
    sorted_kws = []
    with open(sorted_file, 'r') as f:
        sorted_kws = f.read()
    sorted_kws = sorted_kws.split('\n')
    scores = {}
    curr_score = 10000
    first = sorted_kws[0].strip()
    scores[first] = curr_score
    for kw in sorted_kws[1:]:
        second = kw
        print scores
        print "Comparing %s and %s" % (first, second)
        curr_score = scale_score(first, second, curr_score, correction_dict)
        print "Got a score of %d for %s" % (curr_score, second)
        scores[second] = curr_score
        first = second
    return scores
