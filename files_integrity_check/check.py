"""files md5 chk"""
import hashlib
import re
import io
import os
import sys
import time
import traceback
import subprocess


VERSION = 'V1.2 20180318'
MD5_BUF_SIZE = 1024*4
CHK_FILE_NAME = 'filechk.kay'
MSG_LOG_PATH = os.path.abspath(os.path.join(os.path.expanduser('~'), '.Kay/FileIntegrityChk/ErrLog.txt'))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.expanduser('~'), '.Kay/FileIntegrityChk/config.txt'))
ZIP7_DEFAULT_PATH = os.path.abspath('C:/Program Files/7-Zip/7z.exe')

if getattr(sys, 'frozen', False):
    WORKING_DIR_PATH = os.path.dirname(sys.executable)
else:
    WORKING_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_SUFFIX_LIST = ['zip', 'rar', '7z']
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gb18030')  # 兼容文件名中的特殊字符(cmd输出会延迟)

class WorkClass():
    """work dir"""
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.file_list = self.__get_file_list(working_dir)
        self.file_num = len(self.file_list)
        self.total_size = self.__get_total_size()
        self.archives_num = len([archive for archive in self.file_list if archive.split('.')[-1].lower() in ARCHIVE_SUFFIX_LIST])
        self.archives_size = self.__get_archives_size()

    def __get_file_list(self, working_dir):
        """rel path list"""
        file_list = []
        for root, _, files in os.walk(working_dir):
            for filename in files:
                if filename in [CHK_FILE_NAME, os.path.basename(__file__)]:
                    continue
                rel_path = os.path.relpath(os.path.join(root, filename), working_dir)
                file_list.append(rel_path)
        return file_list

    def __get_total_size(self):
        """file size sum, str"""
        total_size = 0
        for rel_path in self.file_list:
            abs_path = os.path.join(self.working_dir, rel_path)
            total_size += os.path.getsize(abs_path)
        return total_size

    def __get_archives_size(self):
        """archives size sum, str"""
        archives_size = 0
        for rel_path in self.file_list:
            if (rel_path.split('.')[-1].lower() not in ARCHIVE_SUFFIX_LIST):
                continue
            abs_path = os.path.join(self.working_dir, rel_path)
            archives_size += os.path.getsize(abs_path)
        return archives_size


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


def get_md5(path):
    """calc md5 of file"""
    md5 = hashlib.md5()
    with open(path, 'rb') as file:
        while True:
            buf = file.read(MD5_BUF_SIZE)
            if buf:
                md5.update(buf)
            else:
                break
    return md5.hexdigest()


def update_chk_data(dir_files):
    """create chk file"""
    if chk_all(dir_files) != 0:
        print('chk file ERROR, create abort. please chk your file.')
        print('create FAILED')
        return 1

    create_start_tm = time.time()
    size_cnt = 0
    print('creating %d files, %s'%(dir_files.file_num, get_readable_size(dir_files.total_size)))
    with open(os.path.join(dir_files.working_dir, CHK_FILE_NAME), 'w', encoding='utf-8') as chk_file:
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        chk_file.write("[{tm}]\n".format(tm=time_now))
        for rel_path in dir_files.file_list:
            file_name = os.path.basename(rel_path)

            try:
                print('{percent:.2f}%({speed:.2f} M/s) | clacing {file} ...'\
                    .format(percent=100 * size_cnt / dir_files.total_size, \
                            speed=size_cnt / (time.time() - create_start_tm + 1) / 1024 / 1024, \
                            file=file_name), end='\t\t\r')
            except UnicodeEncodeError:
                pass
            md5 = get_md5(os.path.join(dir_files.working_dir, rel_path))
            chk_file.write('"{rel_path}":{md5}\n'\
                    .format(rel_path=rel_path, md5=md5))
            size_cnt += os.path.getsize(rel_path)
    print('create tm user: use: {tm:.2f} s, speed: {speed:.2f} M/s\t\t'\
        .format(tm=time.time() - create_start_tm, \
                speed=size_cnt / (time.time() - create_start_tm + 1) / 1024 / 1024))
    print('create OK, %d files added'%dir_files.file_num + '\t'*3)
    return 0


def chk_all(dir_files):
    """chk file with md5 file"""
    chk_file = os.path.join(dir_files.working_dir, CHK_FILE_NAME)
    if not os.path.isfile(chk_file):
        print('chk_file not found!')
        return 0

    chk_start_tm = time.time()

    # get chk list
    with open(chk_file, 'r', encoding='utf-8') as md5_file:
        md5_chk = md5_file.read()
        chk_list = re.findall(r'^"(.*?)":(\w+)', md5_chk, re.M)

    err_msg = ''
    # chk file num
    if len(chk_list) != dir_files.file_num:
        print('file num:%d != chk num:%d'%(dir_files.file_num, len(chk_list)))
    print('chking %d files, %s'%(dir_files.file_num, get_readable_size(dir_files.total_size)))

    # chk missing file
    for chk_rel_path, _ in chk_list:
        if chk_rel_path not in dir_files.file_list:
            msg = 'ERROR: file %s missing!'%chk_rel_path
            err_msg += msg + '\n'
            print(msg)

    # chk md5
    size_cnt = 0
    for file_rel_path in dir_files.file_list:
        try:
            print('{percent:.2f}%({speed:.2f} M/s) | chking {file} ...'\
                .format(percent=100 * size_cnt / dir_files.total_size, \
                        speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024, \
                        file=os.path.basename(file_rel_path)), end='\t\t\r')
        except UnicodeEncodeError:
            pass
        for chk_rel_path, chk_md5 in chk_list:
            if os.path.normpath(chk_rel_path) == os.path.normpath(file_rel_path):
                md5 = get_md5(os.path.join(dir_files.working_dir, file_rel_path))
                if md5 != chk_md5:
                    msg = 'ERROR: file %s chk FAILED!'%file_rel_path
                    err_msg += msg + '\n'
                    print(msg)
                break
        else:
            print('file %s is not in chk file, please update chk file!'%file_rel_path)
        size_cnt += os.path.getsize(file_rel_path)
    print('chk tm use: {tm:.2f} s, speed: {speed:.2f} M/s\t\t'\
        .format(tm=time.time() - chk_start_tm, \
                speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024))

    # write err msg to file
    if err_msg:
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(MSG_LOG_PATH, 'a+', encoding='utf-8') as md5_file:
            md5_file.write('\n[{tm}]\n{msg}'.format(tm=time_now, msg=err_msg))
        print('file chk FAILED' + '\t'*5)
        os.system('start \"\" \"{msg}\"'.format(msg=MSG_LOG_PATH))
        return 1
    else:
        print('file chk OK' + '\t'*5)
        return 0


def test_archives(dir_files, zip7_path):
    """test archive files with md5 file"""
    passwords = input('passwords(separated by \",\"):').split(',')
    if not passwords:
        passwords = ['1']

    print('testing {num} archives, {size}'\
        .format(num=dir_files.archives_num, size=get_readable_size(dir_files.archives_size)))
    err_msg = ''
    chk_start_tm = time.time()
    size_cnt = 0
    for rel_path in dir_files.file_list:
        file_name = os.path.basename(rel_path)
        if (file_name.split('.')[-1].lower() not in ARCHIVE_SUFFIX_LIST):
            continue
        try:
            print('{percent:.2f}%({speed:.2f} M/s) | testing {file} ...'\
                .format(percent=100 * size_cnt / dir_files.archives_size, \
                        speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024, \
                        file=file_name), end='\t\t\r')
        except UnicodeEncodeError:
            pass
        for password in passwords:
            if subprocess.call('\"{zip}\" t -p{pw} \"{file}\" 1>nul 2>nul'\
                .format(zip=zip7_path, pw=password, file=os.path.abspath(rel_path)), shell=True) == 0:
                break
        else: # no matched password
            msg = 'ERROR: archive %s test crc FAILED!'%rel_path
            err_msg += msg + '\n'
            try:
                print(msg)
            except UnicodeEncodeError:
                pass
        size_cnt += os.path.getsize(rel_path)
    print('test tm use: {tm:.2f} s, speed: {speed:.2f} M/s\t\t'\
        .format(tm=time.time() - chk_start_tm, \
                speed=size_cnt / (time.time() - chk_start_tm + 1) / 1024 / 1024))

    # write err msg to file
    if err_msg:
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(MSG_LOG_PATH, 'a+', encoding='utf-8') as md5_file:
            md5_file.write('\n[{tm}]\n{msg}'.format(tm=time_now, msg=err_msg))
        print('archives test FAILED' + '\t'*5)
        os.system('start \"\" \"{msg}\"'.format(msg=MSG_LOG_PATH))
        return 1
    else:
        print('archives test OK' + '\t'*5)
        return 0


def main_proc():
    """main proc"""
    def print_items():
        """echo select items"""
        print('\nworking dir: %s'%WORKING_DIR_PATH)
        print('1.Update %s'%CHK_FILE_NAME)
        print('2.Check files')
        print('3.Test archives')
        print('4.Set 7zip path')
        print('5.Open error message')
        print('c.Clear error message')
        print('d.Delete check file')
        print('0.Quit')

    print('Welcome to file integrity tool. Designed by Kay.')
    print('version: %s'%VERSION)
    print('please wait...')
    if not os.path.isdir(os.path.split(MSG_LOG_PATH)[0]):
        os.makedirs(os.path.split(MSG_LOG_PATH)[0])
    if not os.path.isdir(os.path.split(CONFIG_PATH)[0]):
        os.makedirs(os.path.split(CONFIG_PATH)[0])
    dir_files = WorkClass(WORKING_DIR_PATH)
    print_items()
    while True:
        select = input('->').strip()
        if select == '1':
            try:
                update_chk_data(dir_files)
            except Exception:
                traceback.print_exc()
                print('create aborted unexpected')
        elif select == '2':
            try:
                chk_all(dir_files)
            except Exception:
                traceback.print_exc()
                print('chk aborted unexpected')
        elif select == '3':
            if os.path.isfile(CONFIG_PATH):
                with open(CONFIG_PATH, encoding='utf-8') as file:
                    zip7_path = os.path.abspath(file.read())
            else:
                zip7_path = ZIP7_DEFAULT_PATH
            print('7zip path: %s'%zip7_path)
            try:
                while not os.path.isfile(zip7_path):
                    with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                        zip7_path = file.write(os.path.abspath(zip7_path))
                    os.system('start \"\" \"{conf}\"'.format(conf=CONFIG_PATH))
                    input('7z.exe not found. Please edit path in the file opened now, then save. Press ENTER to continue.')
                    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
                        zip7_path = os.path.abspath(file.read())
                test_archives(dir_files, zip7_path)
            except Exception:
                traceback.print_exc()
                print('test aborted unexpected')
        elif select == '4':
            if not os.path.isfile(CONFIG_PATH):
                with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                    file.write(ZIP7_DEFAULT_PATH)
            os.system('start \"\" \"{conf}\"'.format(conf=CONFIG_PATH))
        elif select == '5':
            if os.path.isfile(MSG_LOG_PATH):
                os.system('start \"\" \"{msg}\"'.format(msg=MSG_LOG_PATH))
            else:
                print('error log empty')
        elif select in ['c', 'C']:
            comfirm = input('Sure to clear err msg?(y/n)').strip()
            if comfirm in ['y', 'Y']:
                if os.path.isfile(MSG_LOG_PATH):
                    os.system('del \"{file}\"'.format(file=MSG_LOG_PATH))
                print('clr done.')
            else:
                print('canceled.')
        elif select in ['d', 'D']:
            comfirm = input('ATTENTION!!! Sure to delet CHECK FILE?(Y/N)').strip()
            if comfirm == 'Y':
                if os.path.isfile(CHK_FILE_NAME):
                    os.system('del \"{file}\"'.format(file=os.path.join(dir_files.working_dir, CHK_FILE_NAME)))
                print('delet done.')
            else:
                print('canceled.')
        elif select in ['0', 'q', 'Q']:
            break
        else:
            print_items()


if __name__ == '__main__':
    main_proc()