#!/usr/bin/env python

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import os
import time

def get_trends(keywords):
    BROWSER_STACK_USERNAME = 'dennislin1'
    BROWSER_STACK_ACCESS_KEY = 'tbZJb61pJZ2S6BFy8bB4'
    BASE_URL = "http://www.google.com/trends/fetchComponent?hl=en-US&q=%s&cid=TIMESERIES_GRAPH_0&export=5&w=500&h=300"
    desired_cap = {'os': 'ANY', 'browser': 'chrome'}

    driver = webdriver.Remote(
            command_executor='http://%s:%s@hub.browserstack.com:80/wd/hub' % (BROWSER_STACK_USERNAME,
                                                                              BROWSER_STACK_ACCESS_KEY),
            desired_capabilities=desired_cap)
    driver.get(BASE_URL % ','.join(keywords))
    html = driver.page_source
    driver.quit()
    return html

def compare(k1, k2, correction_dict={}):
    print "Comparing %s and %s" %(k1, k2)

    keywords = [k1, k2]
    paths = []
    while len(paths) != 2:
        time.sleep(30)
        html = get_trends(keywords)
        if html.find('Not enough search volume to show results.') >= 0:
            return 0
        soup = BeautifulSoup(html, 'html.parser')
        paths = filter(lambda x: x if len(str(x)) > 500 else None, soup.find_all('path'))
        if len(paths) != 2:
            print "FAILED! %s %s" % (k1, k2)

    v1 = 200 - float(paths[0]['d'].split(',')[-1])
    v2 = 200 - float(paths[1]['d'].split(',')[-1])
    for kw in correction_dict.keys():
        correction_factor = correction_dict[kw]
        if k1.lower().startswith(kw):
            v1 = v1 * correction_factor
        if k2.lower().startswith(kw):
            v2 = v2 * correction_factor
    print "%s has a value of %f" % (k1, v1)
    print "%s has a value of %f" % (k2, v2)

    if v1 < v2:
        return -1
    if v1 == v2:
        return 0
    return 1


def get_error_factor(kw, specifier):
    """
    Returns a float which can be used to multiple the more specific of two keywords
    Example:
        - HBase and Apache HBase
        get_error_factor('hbase', 'apache') --> 0.01824
    Multiply # "apache _____" by error factor to get "_____" search frequency

    NOTE: Use very specific kw args in order to properly compare the ratio between
    including the specifier or not
    """
    kws = [kw, specifier + " " + kw]
    paths = []
    while len(paths) != 2:
        time.sleep(30)
        html = get_trends(kws)
        if html.find('Not enough search volume to show results.') >= 0:
            return 0
        soup = BeautifulSoup(html, 'html.parser')
        paths = filter(lambda x: x if len(str(x)) > 500 else None, soup.find_all('path'))
        if len(paths) != 2:
            print "FAILED! %s %s" % (kw, kws[1])
    v1 = 200 - float(paths[0]['d'].split(',')[-1])
    v2 = 200 - float(paths[1]['d'].split(',')[-1])
    return v1/v2


def merge_sort(seq, correction_dict={}):
    """Accepts an array. Utilizes merge sort to sort in place, return
    a sorted sequence"""
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


def sort(kws):
    correction_dict = {}
    correction_dict["apache"] = get_error_factor('hbase', 'apache')
    correction_dict["hashicorp"] = get_error_factor('terraform', 'hashicorp')
    correction_dict["olap"] = get_error_factor('druid', 'olap')
    correction_dict["cloud"] = get_error_factor('terracotta', 'cloud')
    sorted = merge_sort(kws, correction_dict)
    with open('x_sorted.txt', 'a') as f:
        for kw in sorted:
            f.write(kw)
            f.write('\n')
    return sorted

def scale_score(k1, k2, score, correction_dict):
    """
    Takes a score and scales it down
    """
    paths = []
    while len(paths) != 2:
        time.sleep(30)
        html = get_trends([k1, k2])
        if html.find('Not enough search volume to show results.') >= 0:
            return 0
        soup = BeautifulSoup(html, 'html.parser')
        paths = filter(lambda x: x if len(str(x)) > 500 else None, soup.find_all('path'))
        if len(paths) != 2:
            print "FAILED! %s %s" % (kw, kws[1])
    v1 = 200 - float(paths[0]['d'].split(',')[-1])
    v2 = 200 - float(paths[1]['d'].split(',')[-1])
    for kw in correction_dict.keys():
        correction_factor = correction_dict[kw]
        if k1.lower().startswith(kw):
            v1 = v1 * correction_factor
        if k2.lower().startswith(kw):
            v2 = v2 * correction_factor
    return score * v2 / v1

def scoring():
    correction_dict = {}
    correction_dict["apache"] = get_error_factor('hbase', 'apache')
    correction_dict["hashicorp"] = get_error_factor('terraform', 'hashicorp')
    correction_dict["olap"] = get_error_factor('druid', 'olap')
    correction_dict["cloud"] = get_error_factor('terracotta', 'cloud')
    sorted_kws = []
    with open(os.path.join('/', 'Users', 'dlin', 'code', 'osindex', 'sorted.txt'), 'r') as f:
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
