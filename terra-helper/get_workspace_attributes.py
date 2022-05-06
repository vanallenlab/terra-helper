import argparse
import pandas as pd
import sys

import operations
import reformat
from endpoints import gcloud, terra


class Data:
    COLUMN_ORDER = ['namespace', 'name', 'table', 'entity', 'column', 'path']


class Tables(Data):
    @classmethod
    def format_single_row(cls, attributes, tables, table, entity, namespace, name):
        current_row_attributes = []
        for key, value in attributes.items():
            if key in tables:
                continue
            if value is None:
                continue
            elif isinstance(value, (int, float, bool)):
                continue
            elif isinstance(value, str):
                dictionary = {'table': table, 'entity': entity, 'column': key, 'path': value}
                current_row_attributes.append(dictionary)
            elif isinstance(value, dict):
                if 'itemsType' not in value.keys():
                    continue
                if value['itemsType'] == 'AttributeValue':
                    unpacked_dictionary = cls.unpack_dictionary(value['items'], table, entity, key)
                    current_row_attributes.extend(unpacked_dictionary)
                elif value['itemsType'] == 'EntityReference':
                    continue
                else:
                    print("Unexpected itemsType when unpacking dictionary")
                    print(f"{namespace}/{name} in table {table} for entity {entity} and key {key}")
                    sys.exit()
            elif isinstance(value, list):
                unpacked_list = cls.unpack_list(value, table, entity, key)
                current_row_attributes.extend(unpacked_list)
            else:
                print("Unexpected value in data table")
                print(f"{namespace}/{name} in table {table} for entity {entity} and key {key}")
                sys.exit()
        return current_row_attributes

    @classmethod
    def format_to_dataframe(cls, attributes, namespace, name):
        dataframe = pd.DataFrame(attributes)
        dataframe['namespace'] = namespace
        dataframe['name'] = name
        return dataframe.loc[:, cls.COLUMN_ORDER]

    @classmethod
    def format_attributes(cls, rows, tables, namespace, name):
        workspace_attributes = []
        for row in rows:
            attributes = row['attributes']
            if not attributes:
                continue
            table = row['entityType']
            entity = row['name']
            row_attributes = cls.format_single_row(attributes, tables, table, entity, namespace, name)
            row_attributes_gs_paths = cls.subset_attributes_for_gs_paths(row_attributes)
            workspace_attributes.extend(row_attributes_gs_paths)
        return workspace_attributes

    @classmethod
    def get_attributes(cls, workspace):
        namespace = workspace['workspace']['namespace']
        name = workspace['workspace']['name']
        data_table_rows = terra.Terra.request(terra.Terra.get_entities_all_with_type, reformat.Requests.return_json,
                                              namespace=namespace, name=name)
        if not data_table_rows:
            return pd.DataFrame([], columns=Data.COLUMN_ORDER)

        tables = list(set([row['entityType'] for row in data_table_rows]))
        workspace_attributes_records = cls.format_attributes(data_table_rows, tables, namespace, name)
        if not workspace_attributes_records:
            return pd.DataFrame([], columns=Data.COLUMN_ORDER)

        return cls.format_to_dataframe(workspace_attributes_records, namespace, name)

    @staticmethod
    def subset_attributes_for_gs_paths(attributes):
        return [attribute for attribute in attributes if str(attribute['path'])[:5] == "gs://"]

    @staticmethod
    def unpack_dictionary(items, table, entity, key):
        unpacked_records = []
        for item in items:
            record = {'table': table, 'entity': entity, 'column': key, 'path': item}
            unpacked_records.append(record)
        return unpacked_records

    @staticmethod
    def unpack_list(value, table, entity, key):
        unpacked_list = operations.Lists.unpack_while_loop(value)
        unpacked_records = []
        for item in unpacked_list:
            record = {'table': table, 'entity': entity, 'column': key, 'path': item}
            unpacked_records.append(record)
        return unpacked_records


class WorkspaceData(Data):
    @classmethod
    def format_attributes(cls, attributes, namespace, name):
        dataframe = (
            pd
                .Series(attributes, dtype=str)
                .to_frame()
                .reset_index()
                .rename(columns={'index': 'column', 0: 'path'})
        )
        dataframe['namespace'] = namespace
        dataframe['name'] = name
        dataframe['table'] = 'workspace data'
        dataframe['entity'] = pd.NA
        return dataframe.loc[:, cls.COLUMN_ORDER]

    @classmethod
    def get_attributes(cls, workspace, only_bucket_attributes=True):
        namespace = workspace['workspace']['namespace']
        name = workspace['workspace']['name']
        workspace_attributes = workspace['workspace']['attributes']
        if only_bucket_attributes:
            workspace_attributes = cls.subset_attributes(workspace_attributes)
        if workspace_attributes:
            workspace_attributes_formatted = cls.format_attributes(workspace_attributes, namespace, name)
            return workspace_attributes_formatted
        else:
            return cls.format_attributes([], namespace, name)

    @staticmethod
    def subset_attributes(workspace_attributes):
        for key in ['description', 'tag:tags']:
            workspace_attributes.pop(key, None)
        return {key: value for key, value in workspace_attributes.items() if str(value)[:5] == 'gs://'}


def request_workspace(namespace, name):
    return terra.Terra.request(terra.Terra.get_workspace, reformat.Requests.return_json, namespace=namespace, name=name)


def set_data_types(dataframe):
    for column in dataframe.columns:
        dataframe[column] = dataframe[column].astype(str)
    return dataframe


def main(namespace, name):
    workspace = request_workspace(namespace, name)
    workspace_data_attributes = WorkspaceData.get_attributes(workspace)
    workspace_tables_attributes = Tables.get_attributes(workspace)
    return pd.concat([workspace_data_attributes, workspace_tables_attributes], ignore_index=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Record data models',
                                     description='Record all gs:// paths present in data models')
    parser.add_argument('--namespace', '-ns', type=str, required=True, help='workspace namespace')
    parser.add_argument('--name', '-n', type=str, required=True, help='workspace name')
    args = parser.parse_args()

    workspace_namespace = args.namespace
    workspace_name = args.name
    if " " in workspace_name:
        workspace_name = workspace_name.replace(' ', '%20')

    result = main(args.namespace, args.name)
    result.to_csv(f'{workspace_namespace}.{workspace_name}.attributes.tsv', sep='\t', index=False)
