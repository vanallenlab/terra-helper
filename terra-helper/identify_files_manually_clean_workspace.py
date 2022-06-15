import argparse
import pandas as pd

from endpoints import terra


def annotate_attributes(paths, data_model_elements):
    idx = paths.isin(data_model_elements)
    return pd.Series(idx, index=paths, name='in_attributes')


def annotate_file_types_keep(paths, file_types):
    series = pd.Series(paths)
    path_file_types = (
        series
            .astype(str)
            .str.split('/').apply(lambda x: x[-1])
            .str.split('.').apply(lambda x: x[-1])
    )
    file_types = [file_type.lstrip('.') for file_type in file_types]
    idx = path_file_types.isin(file_types)
    idx.name = 'file_type_in_keep_list'
    return pd.concat([pd.Series(paths), idx], axis=1).set_index('path')


def annotate_files_to_clean(dataframe, only_consider_paths_from_submissions):
    idx_attributes = dataframe[dataframe['in_attributes']].index
    idx_submissions = dataframe[dataframe['from_submission']].index
    idx_log = dataframe[dataframe['log']].index
    idx_file_type = dataframe[dataframe['file_type_in_keep_list']].index

    idx_clean = (
        dataframe
        .index
        .difference(idx_attributes)
        .difference(idx_log)
        .difference(idx_file_type)
    )
    idx = idx_clean.intersection(idx_submissions) if only_consider_paths_from_submissions else idx_clean
    idx.name = 'nominated_for_removal'

    series = pd.Series(False, index=dataframe.index, name='nominated_for_removal')
    series.loc[idx] = True
    return series


def annotate_logs(paths):
    series = pd.Series(paths)
    system_files = ['stderr', 'stdout', 'script', 'memory_retry_rc', 'rc', 'output',
                    'gcs_delocalization.sh', 'gcs_localization.sh', 'gcs_transfer.sh']
    idx_system = series.astype(str).str.split('/').apply(lambda x: x[-1]).isin(system_files)
    idx_log = series.astype(str).str[-3:].eq('log')
    idx = idx_system | idx_log
    idx.name = 'log'
    return pd.concat([pd.Series(paths), idx], axis=1).set_index('path')


def annotate_submissions(paths, namespace, name):
    workspace_submissions = request_submissions(namespace, name)
    list_submissions = extract_submission_ids_request(workspace_submissions)
    df = pd.DataFrame(pd.NA, index=paths, columns=list_submissions)
    for submission in list_submissions:
        df.loc[df.index, submission] = pd.Series(df.index, index=df.index, dtype=str).str.contains(submission)
    return df.sum(axis=1).astype(bool)


def extract_submission_ids_request(submission_records):
    return [submission['submissionId'] for submission in submission_records]


def format_booleans_as_integers(dataframe):
    return dataframe.astype(bool).astype(int)


def record_annotations(counts_dataframe, dataframe):
    for column_name in counts_dataframe.columns:
        column_counts = dataframe.loc[:, column_name].astype(bool).value_counts().reindex([True, False], fill_value=0)
        for value in [True, False]:
            counts_dataframe.loc[value, column_name] += column_counts.loc[value]
    return counts_dataframe


def request_submissions(namespace, name):
    return terra.Terra.request(terra.Terra.get_submissions, namespace=namespace, name=name)


def request_workspace(namespace, name):
    return terra.Terra.request(terra.Terra.get_workspace, namespace=namespace, name=name)


def main(namespace, name, attributes, bucket_contents, file_types=None, submissions_only_boolean=True):
    if file_types is None:
        file_types = ['.ipynb']
    bucket_contents = pd.DataFrame(bucket_contents)
    bucket_contents.columns = ['path']
    bucket_contents.set_index('path', inplace=True)

    index = bucket_contents.index
    bucket_contents.loc[index, 'in_attributes'] = annotate_attributes(index, attributes)
    bucket_contents.loc[index, 'from_submission'] = annotate_submissions(index, namespace, name)
    bucket_contents.loc[index, 'log'] = annotate_logs(index)
    bucket_contents.loc[index, 'file_type_in_keep_list'] = annotate_file_types_keep(index, file_types)

    annotation_columns = ['in_attributes', 'from_submission', 'log', 'file_type_in_keep_list']
    annotations = bucket_contents.loc[:, annotation_columns]
    bucket_contents['nominated_for_removal'] = annotate_files_to_clean(annotations, submissions_only_boolean)
    return format_booleans_as_integers(bucket_contents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Clean workspace',
                                     description='Manually identify files from submissions not in attributes to remove')
    parser.add_argument('--namespace', '-ns', type=str, required=True, help='workspace namespace')
    parser.add_argument('--name', '-n', type=str, required=True, help='workspace name')
    parser.add_argument('--attributes', '-a', type=str, required=True, help='workspace attributes')
    parser.add_argument('--bucket-contents', '-b', type=str, required=True, help='workspace bucket contents')
    parser.add_argument('--chunk-size', '-c', type=int, default=10000, help='chunk size for reading bucket contents')
    parser.add_argument('--keep', '-k', nargs='+', action='extend', default=['ipynb'], help='File types to keep')
    parser.add_argument('--print', '-p', action='store_true', help='print details')
    parser.add_argument('--entire-bucket', '-e', action='store_true', help='consider bucket content beyond submissions')
    args = parser.parse_args()
    if args.print:
        print(args)
        print("All files in the workspace's bucket that do not either appear in the data model or as a workspace "
              "annotation will be nominated for cleaning. Please do not have any running jobs.")
        print("")

    workspace_namespace = args.namespace
    workspace_name = args.name
    if " " in workspace_name:
        workspace_name = workspace_name.replace(' ', '%20')

    workspace_attributes = pd.read_csv(args.attributes, sep='\t', usecols=['path'])
    workspace_attributes = workspace_attributes['path'].tolist()

    if args.entire_bucket:
        submissions_only = False
    else:
        submissions_only = True

    columns = ['in_attributes', 'from_submission', 'log', 'file_type_in_keep_list', 'nominated_for_removal']
    counts = pd.DataFrame(0, index=[True, False], columns=columns)

    header = True
    mode = 'w'
    output_name = f'{workspace_namespace}.{workspace_name}.bucket_contents.annotated.tsv'
    for chunk in pd.read_csv(args.bucket_contents, sep='\t', chunksize=args.chunk_size, iterator=True):
        result = main(workspace_namespace, workspace_name, workspace_attributes, chunk, args.keep, submissions_only)
        result.to_csv(output_name, sep='\t', mode=mode, header=header)

        header = False
        mode = 'a'

        counts = record_annotations(counts, result)

    result = pd.read_csv(output_name, sep='\t', usecols=['path', 'nominated_for_removal'])
    nominated_files_to_clean = result[result['nominated_for_removal'].eq(True)].loc[:, 'path']
    nominated_files_to_clean_filename = f'{workspace_namespace}.{workspace_name}.files_to_remove.tsv'
    nominated_files_to_clean.to_csv(nominated_files_to_clean_filename, sep='\t', index=False, header=None)

    if args.print:
        total_files = counts.loc[:, 'in_attributes'].sum()
        print(f"Reporting nominated files to clean for {workspace_namespace}/{workspace_name}")
        print(f"Number of files observed in bucket: {total_files}")

        attribute_count = counts.loc[True, 'in_attributes']
        attribute_pct = round(attribute_count * 100 / total_files, 2)
        print(f"... seen in workspace attributes: {attribute_count} ({attribute_pct}%)")

        submission_count = counts.loc[True, 'from_submission']
        submission_pct = round(submission_count * 100 / total_files, 2)
        print(f"... from workspace submissions: {submission_count} ({attribute_pct}%)")

        log_count = counts.loc[True, 'log']
        log_pct = round(log_count * 100 / total_files, 2)
        print(f"... is a log or from cromwell: {log_count} ({log_pct}%)")

        safe_count = counts.loc[True, 'file_type_in_keep_list']
        safe_pct = round(safe_count * 100 / total_files, 2)
        print(f"... is of file type in the safe list ({', '.join(args.keep)}): {safe_count} ({safe_pct}%)")
        print("")
        print("Keeping files that are either seen in workspace attributes, logs or from cromwell, "
              "or in the file type keep list.")
        print(f"Limiting to files generated from workflow submissions: {args.submissions_only}")

        removal_count = counts.loc[True, 'nominated_for_removal']
        removal_pct = round(removal_count * 100 / total_files, 2)
        print(f"Number of files nominated for removal: {removal_count} ({removal_pct}%)")
        print("")
        print(f"Annotated bucket paths, output file name: {output_name}")
        print(f"Nominated files to remove, output file name: {nominated_files_to_clean_filename}")
        print(f"Review {nominated_files_to_clean_filename} and pass it to remove_files.sh to delete listed files.")
        print(f"Be careful! This process is NOT reversible!")
