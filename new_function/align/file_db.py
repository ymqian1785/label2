import os
from new_function.default_path import *

default_filepath=DefaultPath.defaultFileDBPath

class FileDB:
    def __init__(self,file_path=default_filepath):
        self.file_path=file_path

    def insert_to_info(self,data):
        for list in data:
            data_str=list+";"
        with open(self.file_path,'a') as file:
            file.write(data_str)

    def insert_to_infos(self,datas,mode='a'):
        data_str = ''
        for data in datas:
            for list in data:
                data_str+=(list+';')
            data_str+='\n'
        with open(self.file_path,mode) as file:
            file.write(data_str)

    def select_from_db(self,time):
        with open(self.file_path,'r') as file:
            result_list=file.read()
            for result in result_list:
                res=result.split(';')
                if time==res:
                    return res

    def import_from_db(self):
        photo_list=[]
        with open(self.file_path,'r') as file:
            results=file.readlines()
            for result in results:
                res=result.split(';')
                photo_list.append(res[3])
        return photo_list

    def delete_all_db(self):
        if os.path.exists(self.file_path):
            with open(self.file_path,'r+') as f:
                f.truncate()

    def delete_file(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
