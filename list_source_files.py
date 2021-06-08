import argparse
import pandas as pd


def read_handle(handle, delimiter):
    return pd.read_csv(handle, sep=delimiter)


def subset_copy_log(df):
    return df[df['Result'].eq('OK')]


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Lists source files',
                                         description='Lists files copied successfully with gsutil cp')
    arg_parser.add_argument('--input', '-i', required=True, help='Log from gsutil cp')
    arg_parser.add_argument('--output', '-o', required=True, help='Prefix for output, files successfully copied.')
    arg_parser.add_argument('--bytes', '-b', action='store_true', help='Output bytes transferred.')
    arg_parser.add_argument('--files', '-f', action='store_true', help='Output number of files transferred.')
    args = arg_parser.parse_args()

    log = read_handle(args.input, ',')
    output = f'{args.output}.files_to_remove.txt'
    subset = subset_copy_log(log)

    print(f'{subset.shape[0]} files successfully copied of {log.shape[0]} attempted.')
    print(f'{subset["Bytes Transferred"].sum()} bytes successfully copied of {log["Source Size"].sum()} attempted.')
    print(f'Writing output to {output} in the current working directory.')

    subset['Source'].to_csv(output, sep='\t', index=False, header=False)

    if args.bytes:
        bytes_attempted = log['Source Size'].sum()
        bytes_transferred = subset['Bytes Transferred'].sum()
        gigibytes_attempted = bytes_attempted / 2**30
        gigibytes_transferred = bytes_transferred / 2**30
        pd.Series(bytes_attempted).to_csv('bytes_attempted.txt', index=False, header=False)
        pd.Series(bytes_transferred).to_csv('bytes_transferred.txt', index=False, header=False)
        pd.Series(gigibytes_attempted).to_csv('gigibytes_attempted.txt', index=False, header=False)
        pd.Series(gigibytes_transferred).to_csv('gigibytes_transferred.txt', index=False, header=False)

    if args.files:
        pd.Series(log.shape[0]).to_csv('n_files_attempted.txt', sep='\t', index=False, header=False)
        pd.Series(subset.shape[0]).to_csv('n_files_transferred.txt', sep='\t', index=False, header=False)
