import os
from os import listdir
from os.path import isfile, join, getmtime

def get_file_status(file_status_dir):
    global watches_to_be_created, watches_to_be_deleted, watches_to_be_updated, watches_to_be_disabled, watch_list
    watches_to_be_created = []
    watches_to_be_deleted = []
    watches_to_be_updated = []
    watches_to_be_disabled = []
    watch_list = []
