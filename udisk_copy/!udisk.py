"""main"""
import os
import sys

VERSION = 'V0.1'
DATE = '2017.11.24'

def main():
    """main"""
    print('UDisk {ver}, {dt}'.format(ver=VERSION, dt=DATE))
    print('software path: ', os.path.dirname(sys.argv[0]))
    dist_path = os.path.dirname(sys.argv[0])
    for path in sys.argv[1:]:
        if os.path.samefile(os.path.dirname(path), dist_path): # to del
            if os.path.isfile(path):
                print('delete "{del_file}"'.format(del_file=path))
                os.system('del "{del_file}"'.format(del_file=path))
            if os.path.isdir(path):
                print('delete dir "{del_path}"'.format(del_path=path))
                os.system('rd /S /Q "{del_path}"'.format(del_path=path))
            continue
        if os.path.isfile(path):
            os.system(r'xcopy /Y /F "{from_path}" "{to_path}"'\
                    .format(from_path=path, to_path=dist_path))
        if os.path.isdir(path):
            os.system(r'echo d|xcopy /Y /S /E /F "{from_path}" "{to_path}"'\
                    .format(from_path=path, to_path=os.path.join(dist_path, os.path.basename(path))))

    os.system('pause')

if __name__ == '__main__':
    main()