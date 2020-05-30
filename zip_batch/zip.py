"""zip batch"""
import hashlib
import re
import os
import sys
import time
import traceback
import subprocess


VERSION = 'V1.0 20180131'
ERR_LOG_PATH = os.path.abspath(os.path.join(os.path.expanduser('~'), '.Kay/ZipBatch/ErrLog.txt'))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.expanduser('~'), '.Kay/ZipBatch/config.txt'))
ZIP7_DEFAULT_PATH = os.path.abspath('C:/Program Files/7-Zip/7z.exe')

if getattr(sys, 'frozen', False):
    WORKING_DIR_PATH = os.path.dirname(sys.executable)
else:
    WORKING_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_SUFFIX_LIST = ['zip', 'rar', '7z']


class WorkClass():
    """work dir"""
    def __init__(self, working_dir):
        self.archive_list = self.__get_archive_list(working_dir)
        self.dir_list = self.__get_dir_list(working_dir)
        self.archives_size = self.__get_archives_size()
        self.dirs_size = self.__get_dirs_size()

    def __get_archive_list(self, working_dir):
        """rel path list"""
        _, _, archives = next(os.walk(working_dir))
        archive_list = [x for x in archives if x.split('.')[-1].lower() in ARCHIVE_SUFFIX_LIST]
        print('archive list:', archive_list)
        return archive_list

    def __get_dir_list(self, working_dir):
        """rel path list"""
        _, dirs, _ = next(os.walk(working_dir))
        dir_list = [x for x in dirs]
        print('dir list:', dir_list)
        return dir_list

    def __get_archives_size(self):
        """archives size sum, str"""
        archives_size = 0
        for archive in self.archive_list:
            archives_size += os.path.getsize(archive)
        return archives_size

    def __get_dirs_size(self):
        """dirs size sum, str"""
        dirs_size = 0
        for dir_name in self.dir_list:
            for root, _, files in os.walk(dir_name):
                for filename in files:
                    dirs_size += os.path.getsize(os.path.join(root, filename))
        return dirs_size


def get_dir_size(dir_path):
    """get dir size"""
    dirs_size = 0
    for root, _, files in os.walk(dir_path):
        for filename in files:
            dirs_size += os.path.getsize(os.path.join(root, filename))
    return dirs_size



def get_readable_size(size_byte):
    """get_readable_size"""
    if size_byte < 1024:
        return '%dByte'%size_byte
    elif size_byte < 1024*1024:
        return '%.2fK'%(size_byte / 1024)
    elif size_byte < 1024*1024*1024:
        return '%.2fM'%(size_byte / 1024 / 1024)
    else:
        return '%.2fG'%(size_byte / 1024 / 1024 / 1024)


def extract_archive(work_class, zip7_path):
    """extract_archive"""
    passwords = input('passwords(separated by \",\"):').split(',')
    if not passwords:
        passwords = ['1']
    print('extract {num} archives, {size}'\
        .format(num=len(work_class.archive_list), size=get_readable_size(work_class.archives_size)))
    err_msg = ''
    chk_start_tm = time.time()
    size_cnt = 0
    for archive in work_class.archive_list:
        print('{percent:.2f}%({speed:.2f} M/s) | extracting {file} ...'\
            .format(percent=100 * size_cnt / work_class.archives_size, \
                    speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024, \
                    file=archive), end='\t\t\r')
        for password in passwords:
            if subprocess.call('\"{zpath}\" x -p{pw} -y \"{zname}\" -o\"{dir}\" 1>nul 2>nul'\
                    .format(zpath=zip7_path, pw=password, zname=archive, dir=os.path.splitext(archive)[0]), shell=True) == 0:
                break
        else: # no matched password
            os.system('rm -r \"{dir}\"'.format(dir=os.path.splitext(archive)[0]))
            msg = 'ERROR: archive %s extract FAILED!'%archive
            err_msg += msg + '\n'
            print(msg)
        size_cnt += os.path.getsize(archive)
    print('extract tm use: {tm:.2f} s, speed: {speed:.2f} M/s\t\t'\
        .format(tm=time.time() - chk_start_tm, \
                speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024))

    # write err msg to file
    if err_msg:
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(ERR_LOG_PATH, 'a+') as md5_file:
            md5_file.write('\n[{tm}]\n{msg}'.format(tm=time_now, msg=err_msg))
        print('archives extract FAILED' + '\t'*5)
        os.system('start \"\" \"{msg}\"'.format(msg=ERR_LOG_PATH))
        return 1
    else:
        print('archives extract OK' + '\t'*5)
        return 0


def pack_dir(work_class, zip7_path):
    """pack_dir"""
    password = input('pack password:')
    print('packing {num} dirs, {size}'\
        .format(num=len(work_class.dir_list), size=get_readable_size(work_class.dirs_size)))
    err_msg = ''
    chk_start_tm = time.time()
    size_cnt = 0
    for dir_name in work_class.dir_list:
        print('{percent:.2f}%({speed:.2f} M/s) | packing {dir} ...'\
            .format(percent=100 * size_cnt / work_class.dirs_size, \
                    speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024, \
                    dir=dir_name), end='\t\t\r')
        if subprocess.call('\"{zpath}\" a -t7z {pw} \"{zname}\" \"{dir}\" 1>nul 2>nul'\
                .format(zpath=zip7_path, pw='-p'+password if password else '',\
                    zname=dir_name+'.7z', dir=dir_name), shell=True) != 0:
            msg = 'ERROR: dir %s packing FAILED!'%dir_name
            err_msg += msg + '\n'
            print(msg)
        size_cnt += get_dir_size(dir_name)
    print('extract tm use: {tm:.2f} s, speed: {speed:.2f} M/s\t\t'\
        .format(tm=time.time() - chk_start_tm, \
                speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024))

    # write err msg to file
    if err_msg:
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(ERR_LOG_PATH, 'a+') as md5_file:
            md5_file.write('\n[{tm}]\n{msg}'.format(tm=time_now, msg=err_msg))
        print('dirs packing FAILED' + '\t'*5)
        os.system('start \"\" \"{msg}\"'.format(msg=ERR_LOG_PATH))
        return 1
    else:
        print('dirs packing OK' + '\t'*5)
        return 0


def main_proc():
    """main proc"""
    def print_items():
        """echo select items"""
        print('\nworking dir: %s'%WORKING_DIR_PATH)
        print('1.Unzip all archives')
        print('2.Zip all folders')
        print('3.Set 7zip path')
        print('c.Clear error message')
        print('0.Quit')

    print('Welcome to 7zip batch tool. Designed by Kay.')
    print('version: %s'%VERSION)
    print('please wait...')
    work_class = WorkClass(WORKING_DIR_PATH)
    if not os.path.isdir(os.path.split(ERR_LOG_PATH)[0]):
        os.makedirs(os.path.split(ERR_LOG_PATH)[0])

    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH) as file:
            zip7_path = os.path.abspath(file.read())
    else:
        zip7_path = ZIP7_DEFAULT_PATH
    while not os.path.isfile(zip7_path):
        with open(CONFIG_PATH, 'w') as file:
            zip7_path = file.write(os.path.abspath(zip7_path))
        os.system('start \"\" \"{conf}\"'.format(conf=CONFIG_PATH))
        input('7z.exe not found. Please edit path in the file opened now, then save. Press ENTER to continue.')
        with open(CONFIG_PATH, 'r') as file:
            zip7_path = os.path.abspath(file.read())
    print('7zip path: %s'%zip7_path)

    print_items()
    while True:
        select = input('->').strip()
        if select == '1':
            comfirm = input('press \"y\" to start:').strip()
            if comfirm in ['y', 'Y']:
                extract_archive(work_class, zip7_path)
            else:
                print('canceled.')
        elif select == '2':
            comfirm = input('press \"y\" to start:').strip()
            if comfirm in ['y', 'Y']:
                pack_dir(work_class, zip7_path)
            else:
                print('canceled.')
        elif select == '3':
            os.system('start \"\" \"{conf}\"'.format(conf=CONFIG_PATH))
        elif select in ['c', 'C']:
            comfirm = input('Sure to clear err msg?(y/n)').strip()
            if comfirm in ['y', 'Y']:
                os.system('del \"{file}\"'.format(file=ERR_LOG_PATH))
                print('clr done.')
            else:
                print('canceled.')
        elif select in ['0', 'q', 'Q']:
            break
        else:
            print_items()


if __name__ == '__main__':
    main_proc()