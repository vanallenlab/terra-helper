import argparse
import pandas
import subprocess
import sys
import time


def copy_bucket(log, source, target, mirror_boolean, timeout_boolean):
    if mirror_boolean:
        command = f'gsutil -m cp -L {log} -r gs://{source}/* gs://{target}'
    else:
        command = f'gsutil -m cp -L {log} -r gs://{source} gs://{target}'
    return run_command(command, timeout_boolean)


def run_command(cmd, disable_timeout):
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )
    if disable_timeout:
        stdout, stderr = proc.communicate()
    else:
        # There seems to be an issue that gsutil sometimes hangs
        # I added a timeout of 12 hours, which gosh I can't imagine ever being needed but just in case..
        seconds_twelve_hours = 43200
        stdout, stderr = proc.communicate(timeout=seconds_twelve_hours)
    return proc.returncode, stdout, stderr


def copy(original_bucket, new_bucket, mirror_bool, timeout_bool):
    print('Copying...this could take a while, up to hours, depending on your workspace size.')
    log_handle = f'{original_bucket}-to-{new_bucket}.copy_log.csv'
    return_code, stdout, stderr = copy_bucket(log_handle, original_bucket, new_bucket, mirror_bool, timeout_bool)
    if int(return_code) != int(0):
        print('')
        print(f'stdout: {stdout}')
        print(f'stderr: {stderr}')
        msg = 'Hmm...something went wrong with copying your bucket. Try again or reach out to Brendan. '
        sys.exit(msg)
    else:
        print(f'return code: {return_code}, success!')
        print('')

    return log_handle


def produce_index_for_cleaning(copy_log_handle, files_to_remove_handle):
    df = pandas.read_csv(copy_log_handle)
    shape = df.shape[0]
    df_okay = df[df['Result'].eq('OK')]
    shape_okay = df_okay.shape[0]

    print(f'{shape} files were copied, {shape_okay} were successful.')
    print(f'Creating index file of original files, {files_to_remove_handle}.')
    print('Run cleaner on this file to remove originals that were successfully copied.')

    df['Source'].to_csv(files_to_remove_handle, sep='\t', index=False, header=False)


if __name__ == "__main__":
    start_time = time.time()

    arg_parser = argparse.ArgumentParser(prog='Copy bucket',
                                         description='Copies contents of one Google bucket to another. '
                                                     'An output is produced of all files successfully copied, which '
                                                     'can be passed to the cleaner for removing the original.')
    arg_parser.add_argument('--original', required=True,
                            help='Original bucket; example: fc-894fec90-241f-4069-875d-04da63082465')
    arg_parser.add_argument('--new', required=True,
                            help='Bucket to copy original to; example: fc-d0a0b6ac-b16f-47ca-99eb-49d88a2ba4c2')

    arg_parser.add_argument('--filename', default='files_to_remove.(original bucket).from_copier.txt',
                            help='Filename for files to remove, can be passed to the cleaner.')
    arg_parser.add_argument('--mirror', action='store_true',
                            help='Mirror bucket structure instead of having a folder of the original bucket name.')
    arg_parser.add_argument('--disable_timeout', action='store_true', help='Disable 12 hr timeout from copy')

    args = arg_parser.parse_args()

    input_original = args.original
    input_new = args.new
    input_filename = args.filename
    input_disable_timeout = args.disable_timeout

    if input_original[:5] == 'gs://':
        input_original = input_original[5:]
    if input_new[:5] == 'gs://':
        input_new = input_new[5:]
    if input_original[-1] == '/':
        input_original = input_original[:-1]
    if input_new[-1] == '/':
        input_new = input_new[:-1]

    if input_filename == 'files_to_remove.(original bucket).from_copier.txt':
        input_filename = f'files_to_remove.{input_original}.from_copier.txt'

    log_handle = copy(input_original, input_new, input_disable_timeout)
    produce_index_for_cleaning(log_handle, input_filename)

    end_time = time.time()
    time_statement = "Bucket copy runtime: %s seconds" % round((end_time - start_time), 4)
    print(time_statement)
