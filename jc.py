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

REQ_URL = "https://elkurl/.watches/_search?size=10000"



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

def check_status():
    try:
        res = requests.get(STATUS_URL,headers=REQ_HEADERS,verify ="cert/cert.cert", auth = HTTPBasicAuth(username, password))
        # print(res.content)
        target =res.content
        print(target)
        
    except ConnectionError:
        print("Unable to Connect to API for watch")
        
    except HTTPError as exception:
        print("HTTP Error for watch: "+ str(exception))

    except RequestException as exception:
        print(exception)

def get_existing_elk_watches():
    '''Return current list of project's watch id from elk'''
    try:
        watches_folder = os.path.abspath(os.path.join(getcwd(),"watches"))
        team_list = [team_name for team_name in os.listdir(watches_folder) if os.path.isdir(os.path.join(watches_folder, team_name))] 
        if team_list != 0:
            for team_name in team_list:
                team_folder = os.path.abspath(os.path.join(getcwd(),"watches", team_name))
                project_list = [project for project in os.listdir(team_folder) if os.path.isdir(os.path.join(team_folder, project))]
                if len(project_list) != 0:
                    for project_name in project_list:
                        res = requests.get(SEARCH_URL,headers=REQ_HEADERS,verify ="cert/cert.cert", auth = HTTPBasicAuth(username, password))
                        if res.status_code != 200:
                            raise ConnectionError
                        target = res.content
                        final_target = str(target).replace(" ","").replace("\n","")
                        id_list = re.findall(r'\"_id\"\:"(.*?)"',final_target)
                        required_id_list = []
                        for id in id_list:
                            if re.search(rf'.*{team_name}.*{project_name}.*',id, re.IGNORECASE):
                                required_id_list.append(id)
                        return required_id_list
    
    except ConnectionError:
        print("Unable to Connect to API for watch")
        
    except HTTPError as exception:
        print("HTTP Error for watch: "+ str(exception))

    except RequestException as exception:
        print(exception)

def activate_watch(watch_id):
    '''Enable watch'''
    try:
        res = requests.put(ACTION_URL + watch_id +"/_activate", headers=REQ_HEADERS,verify ="cert/cert.cert", auth = HTTPBasicAuth(username, password))
        target =res.content
        print(target)
        
    except ConnectionError:
        print("Unable to Connect to API for watch")
        
    except HTTPError as exception:
        print("HTTP Error for watch: "+ str(exception))

    except RequestException as exception:
        print(exception)
        
def deactivate_watch(watch_id) :
    '''Disable watch'''
    try:
        res = requests.put(ACTION_URL + watch_id +"/_deactivate", headers=REQ_HEADERS,verify ="cert/cert.cert", auth = HTTPBasicAuth(username, password))
        target = res.content
        json_target = json.loads(target)
        print(json_target)
        # if json_target["status"]["state"]["active"]:
        #     print("Watch with id {} id is activated\n".format(watch_id))
        # else:
        #     print("Watch with id {} id is deactivated\n".format(watch_id))
    except ConnectionError:
        print("Unable to Connect to API for watch")
        
    except HTTPError as exception:
        print("HTTP Error for watch: "+ str(exception))

    except RequestException as exception:
        print(exception)
        
def delete_watch(watch_id):
    '''Delete watch'''
    try:
        print(watch_id)
        res = requests.delete(ACTION_URL + watch_id, headers=REQ_HEADERS,verify ="cert/cert.cert", auth = HTTPBasicAuth(username, password))
        target =res.content
        json_target = json.loads(target)
        print(json_target)
        # if json_target["found"]:
        #     print("Deleted watch with id {} succesfully\n".format(watch_id))
        # else:
        #     print("Could not find watch with id {}\n".format(watch_id))
    except ConnectionError:
        print("Unable to Connect to API for watch")
        
    except HTTPError as exception:
        print("HTTP Error for watch: "+ str(exception))

    except RequestException as exception:
        print(exception)
 
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
            
def create_or_update_watch(watch_id, data):
    try:
        res = requests.put(ACTION_URL + watch_id, data = json.dumps(data), headers=REQ_HEADERS,verify ="cert/cert.cert", auth = HTTPBasicAuth(username, password))
        target =res.content
        json_target = json.loads(target)
        print(json_target)
        # if json_target["created"]:
        #     print("Created watch with id {} succesfully\n".format(watch_id))
        # else:
        #     print("Updated watch with id {}\n".format(watch_id))
    except ConnectionError:
        print("Unable to Connect to API for watch")
        
    except HTTPError as exception:
        print("HTTP Error for watch: "+ str(exception))

    except RequestException as exception:
        print(exception)

def deactivate_watches_from_list(target_list):
    if len(target_list) != 0:
        for watch in target_list:
            # print("Deactivating watch :", str(watch))
            deactivate_watch(watch)
    
def delete_watches_from_list(target_list):
    if len(target_list) != 0:
        for watch in target_list:
            # print("Deteting watch :", str(watch))
            delete_watch(watch)

def create_watches_from_list(target_list):    
    local_watch_dict = get_local_watch_id_dict()
    # existing_watchs = get_existing_project_watchs()
    if len(target_list) != 0:
        for watch in target_list:
            watch_dir = local_watch_dict[watch]
            watch_data = parse_es_to_json(watch_dir)
            # print("Creating watch :", str(watch))
            create_or_update_watch(watch, watch_data)
        
def update_watches_from_list(target_list):
    # repo_watch_dict = get_local_watch_id_dict(team_name)
    # existing_watchs = get_existing_project_watchs()
    # for watch in target_list:
    #     if watch not in existing_watchs:
    #         watch_dir = repo_watch_dict[watch]
    #         watch_data = parse_es_to_json(watch_dir)
    #         create_or_update_watch(watch, watch_data)
    
    local_watch_dict = get_local_watch_id_dict()
    # existing_watchs = get_existing_project_watchs()
    if len(target_list) != 0:
        for watch in target_list:
            watch_dir = local_watch_dict[watch]
            watch_data = parse_es_to_json(watch_dir)
            # print("Updating watch :", str(watch))
            create_or_update_watch(watch, watch_data)
# def main(argv):
    
if __name__ == '__main__':
    username = sys.argv[1]
    password = sys.argv[2]
    BASE_URL = sys.argv[3].encode().decode('unicode_escape')
    # STATUS_URL = BASE_URL + "_cluster/health?pretty=true"
    SEARCH_URL = BASE_URL + ".watches/_search?size=10000"

    ACTION_URL = BASE_URL + "_watcher/watch/"

    REQ_HEADERS = {'content-type': 'application/json'}
    file_status_dir = os.path.abspath(os.path.join(getcwd(),"file_status_log"))
    get_file_status(file_status_dir)
    print("watches to be created:\n", watches_to_be_created)
    print("watches to be deleted:\n", watches_to_be_deleted)
    print("watches to be updated:\n", watches_to_be_updated)
    print("watches to be disabled:\n", watches_to_be_disabled)
    print("watch list\n", watch_list)
    create_watches_from_list(watches_to_be_created)
    update_watches_from_list(watches_to_be_updated)
    delete_watches_from_list(watches_to_be_deleted)
    deactivate_watches_from_list(watches_to_be_disabled)
    # print("Existing watch in elk")
    # print(get_existing_elk_watches())
    # create_missing_watches()
    # delete_unused_watches()
    # os.remove(file_status_dir)
