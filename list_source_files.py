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
    args = arg_parser.parse_args()

    log = read_handle(args.input, ',')
    output = f'{args.output}.files_to_remove.txt'
    subset = subset_copy_log(log)

    print(f'{subset.shape[0]} files successfully copied of {log.shape[0]} attempted.')
    print(f'{subset["Bytes Transferred"].sum()} bytes successfully copied of {log["Source Size"].sum()} attempted.')
    print(f'Writing output to {output} in the current working directory.')

    subset['Source'].to_csv(output, sep='\t', index=False, header=False)
