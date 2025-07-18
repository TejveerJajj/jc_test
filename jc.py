import requests
import re
import json
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, HTTPError
from os import listdir, getcwd
from os.path import isfile, join, getmtime
import os
import sys
from get_file_status import *
from config import Config



def get_local_watch_id_dict():
    """Return watch ids into dict with id as key, watch dir as value"""
    watch_dict= {}
    watches_folder = os.path.abspath(os.path.join(getcwd(),"watches"))
    team_list = [team_name for team_name in os.listdir(watches_folder) if os.path.isdir(os.path.join(watches_folder, team_name))]
    # print(team_list)
    if team_list != 0:
        for team_name in team_list:
            team_folder = os.path.abspath(os.path.join(getcwd(),"watches", team_name))
            project_list = [project for project in os.listdir(team_folder) if os.path.isdir(os.path.join(team_folder, project))]
            # print(project_list)
            if len(project_list) != 0:
                for project_name in project_list:
                    project_folder = os.path.abspath(os.path.join(getcwd(),"watches", team_name, project_name))
                    # print(project_folder)
                    piority_list = [piority for piority in os.listdir(project_folder) if os.path.isdir(os.path.join(project_folder, piority))]
                    # print(piority_list)
                    if len(piority_list) != 0:
                        for piority in piority_list:
                            piority_folder = os.path.abspath(os.path.join(getcwd(),"watches", team_name, project_name, piority))
                            for description in listdir(piority_folder):
                                watch_path = join(piority_folder, description) 
                                watch_id = team_name + "_" + project_name + "_" + piority + "_" + description.split(".")[0]
                                watch_dict[watch_id] = watch_path
    return watch_dict
def get_local_watch_id_list():
    """Return the list of watch id in local watchs folder"""
    return [*get_local_watch_id_dict()]

def parse_es_to_json(target_file_dir):
    """ Remove breaking lines except for the content within triple quotes, add escape to double-quotes inside tripple quotes then return to json data"""
    with open(target_file_dir,"r") as f:
        data= f.readlines()
        begining_of_tripple_quotes = True
        content_witin_tripe_quotes = False
        flag_of_condition = False
        # Iterate lines within watch file
        for i in range(0,len(data)-1):
            # set flag if it's checking contents after condition
            if re.match(r'.*\"condition\".*',data[i]):
                flag_of_condition = True
            if flag_of_condition:
                # skip triple quotes starts and closes in one line
                # update flags if it's iterating content within triple quotes
                if re.match(r'.*\"{3}.*',data[i]) and len(re.findall(r'\"{3}',data[i])) == 1:
                    if begining_of_tripple_quotes:
                        begining_of_tripple_quotes = False
                        content_witin_tripe_quotes = True
                    # update flags it's the close of triple quotes
                    else:
                        begining_of_tripple_quotes = True
                        content_witin_tripe_quotes = False
                        # add newline for the close of triple quotes
                        data[i] = "\\n"+ data[i]
                else:
                    # add escape char to \n for the lines within triple quotes
                    if content_witin_tripe_quotes:
                        data[i] = "\\n"+ data[i]
        # remove \n without escap chars, and join them into a string
        update_data = [line.replace("\n", "") for line in data]
        data_string = "".join(update_data)
        # search content within triple quotes
        matches = re.findall(r'\"{3}(.*?)\"{3}',data_string)
        for target_string in matches:
            # add escape chars to double quotes within triples
            temp_result = target_string.replace('\"','\\\"')
            data_string = data_string.replace(target_string, temp_result)
        # replace triple quotes with doubles so it could be uploadable.
        result = data_string.replace('"""','"')
    return json.loads(result)

def check_status(config):
    try:
        res = requests.get(config.search_url, headers=config.req_headers, verify=config.cert_path, auth=HTTPBasicAuth(config.username, config.password))
        res.raise_for_status()
        target = res.content
        print(target)
    except (ConnectionError, HTTPError, RequestException) as e:
        print(f"Error checking status: {e}")

def get_existing_elk_watches(config):
    '''Return current list of project's watch id from elk'''
    try:
        watches_folder = os.path.abspath(os.path.join(getcwd(), "watches"))
        team_list = [team_name for team_name in os.listdir(watches_folder) if os.path.isdir(os.path.join(watches_folder, team_name))]
        if team_list:
            for team_name in team_list:
                team_folder = os.path.abspath(os.path.join(getcwd(), "watches", team_name))
                project_list = [project for project in os.listdir(team_folder) if os.path.isdir(os.path.join(team_folder, project))]
                if project_list:
                    for project_name in project_list:
                        res = requests.get(config.search_url, headers=config.req_headers, verify=config.cert_path, auth=HTTPBasicAuth(config.username, config.password))
                        res.raise_for_status()
                        target = res.content
                        final_target = str(target).replace(" ", "").replace("\n", "")
                        id_list = re.findall(r'\"_id\"\:"(.*?)"', final_target)
                        required_id_list = [id for id in id_list if re.search(rf'.*{team_name}.*{project_name}.*', id, re.IGNORECASE)]
                        return required_id_list
    except (ConnectionError, HTTPError, RequestException) as e:
        print(f"Error getting existing ELK watches: {e}")

def activate_watch(config, watch_id):
    '''Enable watch'''
    try:
        res = requests.put(f"{config.action_url}{watch_id}/_activate", headers=config.req_headers, verify=config.cert_path, auth=HTTPBasicAuth(config.username, config.password))
        res.raise_for_status()
        target = res.content
        print(target)
    except (ConnectionError, HTTPError, RequestException) as e:
        print(f"Error activating watch {watch_id}: {e}")

def deactivate_watch(config, watch_id):
    '''Disable watch'''
    try:
        res = requests.put(f"{config.action_url}{watch_id}/_deactivate", headers=config.req_headers, verify=config.cert_path, auth=HTTPBasicAuth(config.username, config.password))
        res.raise_for_status()
        target = res.content
        json_target = json.loads(target)
        print(json_target)
    except (ConnectionError, HTTPError, RequestException) as e:
        print(f"Error deactivating watch {watch_id}: {e}")

def delete_watch(config, watch_id):
    '''Delete watch'''
    try:
        print(watch_id)
        res = requests.delete(f"{config.action_url}{watch_id}", headers=config.req_headers, verify=config.cert_path, auth=HTTPBasicAuth(config.username, config.password))
        res.raise_for_status()
        target = res.content
        json_target = json.loads(target)
        print(json_target)
    except (ConnectionError, HTTPError, RequestException) as e:
        print(f"Error deleting watch {watch_id}: {e}")
 
def delete_unused_watches():
    for elk_watch in get_existing_elk_watches():
        if elk_watch not in get_local_watch_id_list():
            print("Found unused watch with id:{}".format(elk_watch))
            delete_watch(elk_watch)
            
def create_missing_watches():
    for local_watch in get_local_watch_id_list():
        if local_watch not in get_existing_elk_watches():
            print("Found missing watch with id:{}".format(local_watch))
            # create_or_update_watch(local_watch)
            
def create_or_update_watch(config, watch_id, data):
    try:
        res = requests.put(f"{config.action_url}{watch_id}", data=json.dumps(data), headers=config.req_headers, verify=config.cert_path, auth=HTTPBasicAuth(config.username, config.password))
        res.raise_for_status()
        target = res.content
        json_target = json.loads(target)
        print(json_target)
    except (ConnectionError, HTTPError, RequestException) as e:
        print(f"Error creating or updating watch {watch_id}: {e}")

def deactivate_watches_from_list(config, target_list):
    if target_list:
        for watch in target_list:
            deactivate_watch(config, watch)

def delete_watches_from_list(config, target_list):
    if target_list:
        for watch in target_list:
            delete_watch(config, watch)

def create_watches_from_list(config, target_list):
    local_watch_dict = get_local_watch_id_dict()
    if target_list:
        for watch in target_list:
            watch_dir = local_watch_dict[watch]
            watch_data = parse_es_to_json(watch_dir)
            create_or_update_watch(config, watch, watch_data)

def update_watches_from_list(config, target_list):
    local_watch_dict = get_local_watch_id_dict()
    if target_list:
        for watch in target_list:
            watch_dir = local_watch_dict[watch]
            watch_data = parse_es_to_json(watch_dir)
            create_or_update_watch(config, watch, watch_data)

def main():
    if len(sys.argv) != 4:
        print("Usage: python jc.py <username> <password> <base_url>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    base_url = sys.argv[3].encode().decode('unicode_escape')

    config = Config(username, password, base_url)

    file_status_dir = os.path.abspath(os.path.join(getcwd(), "file_status_log"))
    get_file_status(file_status_dir)

    print("watches to be created:\n", watches_to_be_created)
    print("watches to be deleted:\n", watches_to_be_deleted)
    print("watches to be updated:\n", watches_to_be_updated)
    print("watches to be disabled:\n", watches_to_be_disabled)
    print("watch list\n", watch_list)

    create_watches_from_list(config, watches_to_be_created)
    update_watches_from_list(config, watches_to_be_updated)
    delete_watches_from_list(config, watches_to_be_deleted)
    deactivate_watches_from_list(config, watches_to_be_disabled)

if __name__ == '__main__':
    main()
