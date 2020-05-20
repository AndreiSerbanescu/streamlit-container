import json
from common import utils
import os
from time import sleep

class CommanderHandler:

    def __init__(self, config_in_dir, result_dir):
        self.config_in_dir = config_in_dir
        self.result_dir = result_dir

        os.makedirs(config_in_dir, exist_ok=True)
        os.makedirs(result_dir, exist_ok=True)

    def call_commander(self, project_name, soure_dir, workers_selected, fat_interval):

        config_json = self.__generate_config_json(project_name, soure_dir, workers_selected, fat_interval)
        config_id = utils.get_unique_id()

        config_name = f"config-{config_id}.json"
        config_fullpath = os.path.join(self.config_in_dir, config_name)

        self.__write_config(config_fullpath, config_json)
        return self.__watch_for_result_json(config_id)

    def __watch_for_result_json(self, config_id):

        result_name = f"result-{config_id}"

        while True:
            files = os.listdir(self.result_dir)
            for file in files:
                if file == result_name:
                    filepath = os.path.join(self.result_dir, file)

                    return self.__extract_info_from_result_file(filepath)

            sleep(0.5)

    def __extract_info_from_result_file(self, file):

        with open(file) as result_file:
            data = json.load(result_file)

        paths = data["paths"]
        workers_not_ready = data["workers_not_ready"]
        workers_failed = data["workers_failed"]

        return paths, workers_not_ready, workers_failed

    def __write_config(self, config_fullpath, config_json):

        print("writing config file")
        with open(config_fullpath, 'w') as outfile:
            json.dump(config_json, outfile)

    def __generate_config_json(self, project_name, source_dir, workers_selected, fat_interval):

        contents = {
            "source_filepath": source_dir,
            "project_name": project_name,
            "workers_selected": workers_selected
        }

        if fat_interval is not None:
            contents["fat_interval"] = fat_interval

        return json.dumps(contents)