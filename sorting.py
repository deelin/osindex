#!/usr/bin/env python

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import time

def compare(k1, k2):
    BROWSER_STACK_USERNAME = 'dennislin1'
    BROWSER_STACK_ACCESS_KEY = 'tbZJb61pJZ2S6BFy8bB4'
    desired_cap = {'os': 'ANY', 'browser': 'chrome'}

    keywords = [k1, k2]
    BASE_URL = "http://www.google.com/trends/fetchComponent?hl=en-US&q=%s&cid=TIMESERIES_GRAPH_0&export=5&w=500&h=300"

    paths = []
    while len(paths) != 2:
        time.sleep(30)
        driver = webdriver.Remote(
                command_executor='http://dennislin1:tbZJb61pJZ2S6BFy8bB4@hub.browserstack.com:80/wd/hub',
                desired_capabilities=desired_cap)
        driver.get(BASE_URL % ','.join(keywords))
        html = driver.page_source
        driver.quit()

        if html.find('Not enough search volume to show results.') >= 0:
            return 0
        soup = BeautifulSoup(html, 'html.parser')
        paths = filter(lambda x: x if len(str(x)) > 500 else None, soup.find_all('path'))
        if len(paths) != 2:
            print "FAILED! %s %s" % (k1, k2)

    v1 = float(paths[0]['d'].split(',')[-1])
    v2 = float(paths[1]['d'].split(',')[-1])
    print "Comparing %s and %s" %(k1, k2)
    if v1 < v2:
        return -1
    if v1 == v2:
        return 0
    return 1


def merge_sort(seq):
    """Accepts a mutable sequence. Utilizes merge sort to sort in place, return
    a sorted sequence"""
    if len(seq) == 1:
        return seq
    else:
        #recursion: break sequence down into chunks of 1
        mid = len(seq)/2
        left = merge_sort(seq[:mid])
        right = merge_sort(seq[mid:])

        i, j, k = 0, 0, 0 #i= left counter, j= right counter, k= master counter

        #run until left or right is out
        while i < len(left) and j < len(right):
            #if current left val is < current right val; assign to master list
            if compare(left[i], right[j]) <= 0:
                seq[k] = left[i]
                i += 1; k += 1
            #else assign right to master
            else:
                seq[k] = right[j]
                j += 1; k += 1

        #handle remaining items in remaining list
        remaining = left if i < j else right
        r = i if remaining == left else j

        while r < len(remaining):
            seq[k] = remaining[r]
            r += 1; k += 1

        return seq
