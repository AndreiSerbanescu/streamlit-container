import os
from workers.converter import Converter
import csv
import subprocess as sb

class CTFatMeasurer:

    def __init__(self, container_requester):
        self.container_requester = container_requester

        self.worker_hostname = os.environ["CT_FAT_MEASURE_HOSTNAME"]
        self.worker_port     = os.environ["CT_FAT_MEASURE_PORT"]
        self.nifti_measure_request_name = "ct_visceral_fat_nifti"
        self.dcm_measure_request_name   = "ct_visceral_fat_dcm"

        self.converter = Converter(self.container_requester)

    def measure_nifti(self, source_file, filepath_only=False):
        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"
        return self.__ct_fat_measure(source_file, request_name=self.nifti_measure_request_name,
                                     filepath_only=filepath_only)

    def measure_dcm(self, source_file, filepath_only=False):
        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

        nifti_filename = self.converter.convert_dcm_to_nifti(source_file)
        return self.__ct_fat_measure(nifti_filename, request_name=self.nifti_measure_request_name,
                                     filepath_only=filepath_only)

    def __ct_fat_measure(self, source_file, request_name, filepath_only):
        payload = {"source_file": source_file}

        response_dict = self.container_requester.send_request_to_worker(payload,
                                                                        self.worker_hostname,
                                                                        self.worker_port,
                                                                        request_name)

        relative_report_path = response_dict["fat_report"]
        data_share = os.environ["DATA_SHARE_PATH"]
        report_path = os.path.join(data_share, relative_report_path)

        print("Report path")

        if filepath_only:
            return report_path

        report_csv = self.__read_csv_file(report_path)
        self.__delete_file(report_path)

        return report_csv

    def __read_csv_file(self, filepath):

        with open(filepath) as csv_file:
            lines = csv_file.readlines()
            # remove all whitespaces
            lines = [line.replace(' ', '') for line in lines]

            csv_dict = csv.DictReader(lines)
            dict_rows = []
            for row in csv_dict:
                dict_rows.append(row)

            return dict_rows

    # TODO error handling?
    def __delete_file(self, filepath):

        rm_cmd = "rm -rf {}".format(filepath)
        print("Removing {}".format(filepath))
        sb.call([rm_cmd], shell=True)


# def ct_fat_measure_nifti(source_file, filepath_only=False, split=False):
#     assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"
#
#     assert __is_nifti(source_file)
#     return __ct_fat_measure(source_file, "ct_visceral_fat_nifti", filepath_only=filepath_only)
#
#
# def ct_fat_measure_dcm(source_file, filepath_only=False, split=False):
#     assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"
#
#     # if split:
#     #     return __ct_fat_measure_dcm_split(source_file, filepath_only=filepath_only)
#
#     return __ct_fat_measure_dcm_single(source_file, filepath_only=filepath_only)
#
#
#
# def  __ct_fat_measure_dcm_single(source_file, filepath_only):
#     nifti_filename = __converter_convert_dcm_to_nifti(source_file)
#     return __ct_fat_measure(nifti_filename, "ct_visceral_fat_nifti", filepath_only=filepath_only)
#
# # def __ct_fat_measure_dcm_split(source_file, filepath_only):
# #
# #
# #     #TODO fix infinite threads
# #     dcm_files = sorted(os.listdir(source_file))
# #     file_no = len(dcm_files)
# #     split_no = 4
# #     file_no_in_split = math.ceil(file_no / split_no)
# #
# #     intervals = []
# #     for i in range(split_no):
# #         intervals.append((i * file_no_in_split, min((i + 1) * file_no_in_split, file_no)))
# #
# #     data_share = os.environ["DATA_SHARE_PATH"]
# #     unique_file = "streamlit-fat-measure-split_" + str(time())
# #
# #     base_dir = os.path.join(data_share, unique_file)
# #     os.makedirs(unique_file, exist_ok=False)
# #
# #     split_dirs = []
# #     for i in range(split_no):
# #         interval = intervals[i]
# #         sub_dir = str(i)
# #         split_dir = os.path.join(base_dir, sub_dir)
# #
# #         os.makedirs(split_dir, exist_ok=False)
# #
# #         split_dirs.append(split_dir)
# #
# #         __ct_fat_measure_move_files(source_file, interval, split_dir)
# #
# #     threads = []
# #
# #     queue = Queue()
# #
# #     for i in range(len(split_dirs)):
# #         split_dir = split_dirs[i]
# #
# #         def fat_measure_wrapper(split_dir, id):
# #             csv_report = __ct_fat_measure_dcm_split(split_dir, filepath_only=False)
# #             return csv_report, id
# #
# #         thread = Thread(target=lambda q: q.put(fat_measure_wrapper(split_dir, i)),
# #                         args=(queue,))
# #
# #         threads.append(thread)
# #         thread.start()
# #
# #     for thread in threads:
# #         thread.join()
# #
# #     csv_reports = {}
# #     while not queue.empty():
# #         csv_report, id = queue.get()
# #         csv_reports[id] = csv_reports
# #
# #
# #     agg_report = __ct_fat_measure_aggregate_split_reports(csv_reports)
# #
# #     if filepath_only:
# #         # TODO write to file
# #         pass
# #
# #     return agg_report
#
# def __ct_fat_measure_aggregate_split_reports(csv_reports):
#     print(csv_reports[0])
#     return None
#
# def __ct_fat_measure_move_files(dcm_files_directory, interval, split_dir):
#
#     dcm_files = sorted(os.listdir(dcm_files_directory))
#     start, end = interval
#
#     for i in range(start, end):
#         dcm_file = dcm_files[i]
#         dcm_filename = os.path.split(dcm_file)[1]
#         copyfile(os.path.join(dcm_files_directory, dcm_file), os.path.join(split_dir, dcm_filename))



