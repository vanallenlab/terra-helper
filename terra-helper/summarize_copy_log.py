import argparse
import pandas as pd


def read(handle):
    return pd.read_csv(handle, low_memory=False)


def write(value, filename):
    pd.Series(value).to_csv(filename, sep='\t', index=False, header=False)


def main(df, write_outputs=False):
    succeeded = df[df['Result'].eq('OK')]

    bytes_attempted = df['Source Size'].sum()
    bytes_success = succeeded['Bytes Transferred'].sum()

    n_files_attempted = df.shape[0]
    n_files_success = succeeded.shape[0]
    print(f'Attempted: {n_files_attempted} files, {bytes_attempted} bytes')
    print(f'Successfully transferred: {n_files_success} files, {bytes_success} bytes')

    if write_outputs:
        write(bytes_attempted, 'bytes_attempted.txt')
        write(bytes_success, 'bytes_success.txt')
        write(n_files_attempted, 'n_files_attempted.txt')
        write(n_files_success, 'n_files_success.txt')

    all_files_succeeded = n_files_attempted == n_files_success
    all_bytes_succeeded = bytes_attempted == bytes_success
    print(f'All files attempted successfully transferred: {all_files_succeeded}')
    print(f'All bytes attempted successfully transferred: {all_bytes_succeeded}')

    if write_outputs:
        write(all_files_succeeded, 'all_files_succeeded.txt')
        write(all_bytes_succeeded, 'all_bytes_succeeded.txt')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='summarize_copy_log.py', description='Summarize gsutil copy')
    parser.add_argument('--input', '-i', required=True, help='gsutil copy log')
    parser.add_argument('--output', '-o', action="store_true", help='produce output files')
    args = parser.parse_args()

    dataframe = read(args.input)
    main(dataframe, args.output)
