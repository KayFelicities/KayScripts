"""md5sum"""
import sys
import os
import time
import traceback
import hashlib
import getopt

def get_md5(path):
    """calc md5 of file"""
    md5 = hashlib.md5()
    with open(path, 'rb') as file:
        while True:
            buf = file.read(1024*1024)
            if buf:
                md5.update(buf)
            else:
                break
    return md5.hexdigest()

def md5sum(dir_path):
    """md5sum"""
    files = [x for x in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, x))]
    content = ''
    for file in files:
        content += get_md5(os.path.join(dir_path, file)) + '  ' + file + '\n'
    return content

if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "o:n:")
        if not args or not os.path.isdir(args[0]):
            raise Exception('ERROR: 请将需要计算md5的文件夹拖到本软件上进行计算')
        working_dir = os.path.abspath(args[0])
        out_file_path = working_dir
        out_file_name = 'bin.md5'
        for op, value in opts:
            if op == '-o':
                out_file_path = os.path.abspath(value)
            if op == '-n':
                out_file_name = value
        
        # del old md5 file 
        old_md5_file = os.path.join(working_dir, out_file_name)
        if os.path.isfile(old_md5_file):
            os.remove(old_md5_file)

        # write md5 file
        out_file = os.path.join(out_file_path, out_file_name)
        print('calcing dir: {dir}, output: {out}'.format(dir=working_dir, out=out_file))
        content = md5sum(working_dir)
        with open(out_file, 'w', newline='\n') as md5file:
            md5file.write(content)
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        os.system('color 47')
        time.sleep(3)
        os.system('color 07')
        sys.exit(1)