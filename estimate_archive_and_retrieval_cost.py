import argparse
import pandas as pd
import index_workspace

root = 'https://api.firecloud.org/api'

# https://cloud.google.com/storage/pricin
# STORAGE COSTS  costs are GB per month

US = 'us'
US_CENTRAL = 'us-central1'
STANDARD = 'standard'
NEARLINE = 'nearline'
COLDLINE = 'coldline'
ARCHIVE = 'archive'

LOCATIONS = [US, US_CENTRAL]
STORAGE_TYPES = [STANDARD, NEARLINE, COLDLINE, ARCHIVE]

STORAGE_COSTS = {
    US: {
        STANDARD: 0.026,
        NEARLINE: 0.010,
        COLDLINE: 0.007,
        ARCHIVE: 0.004
    },
    US_CENTRAL: {
        STANDARD: 0.020,
        NEARLINE: 0.010,
        COLDLINE: 0.004,
        ARCHIVE: 0.0012
    }
}

# NETWORK EGRESS COSTS, cost per GB
NETWORK = {
    US: 0,  # US TO CENTRAL
    US_CENTRAL: 0.01  # CENTRAL TO US
}
# https://cloud.google.com/storage/pricing#network-pricing
# network egress suggests multi region > region is free but not region > multi region

MINIMUM_DURATION = {
    STANDARD: 0,
    NEARLINE: 30,
    COLDLINE: 90,
    ARCHIVE: 365
}

RETRIEVAL_COST = {
    STANDARD: 0,
    NEARLINE: 0.01,
    COLDLINE: 0.02,
    ARCHIVE: 0.05
}

# Class A operation costs per 10,000 operations
OPERATION_A_COST = {
    STANDARD: 0.05,
    NEARLINE: 0.10,
    COLDLINE: 0.10,
    ARCHIVE: 0.50
}

# Class B operation costs per 10,000 operations
OPERATION_B_COST = {
    STANDARD: 0.004,
    NEARLINE: 0.01,
    COLDLINE: 0.05,
    ARCHIVE: 0.50
}


def adjust_daily_storage_charge(dataframe):
    df = dataframe.copy(deep=True)
    columns = df.columns[1:]
    for storage_type in STORAGE_TYPES:
        min_duration = MINIMUM_DURATION[storage_type]
        idx = (slice(None), storage_type)
        df.loc[idx, columns[:min_duration + 1]] = df.loc[idx, columns[min_duration]]
    return df


def adjust_storage_charge_fees(time_scale, dataframe, fees_breakdown):
    duration = 550 if time_scale == 'day' else 19

    df = dataframe.copy(deep=True)
    units = df.columns[-duration:]

    for location in LOCATIONS:
        for storage_type in STORAGE_TYPES:
            idx = (location, storage_type)
            df.loc[idx, units] = df.loc[idx, units].add(fees_breakdown.loc[idx, 'fees_total'])
    return df


def calculate_fees(network, a_operations, retrieval):
    # fees to archive from multi regional standard = network_to + operations_to
    # fees to retrieve from multi regional standard = network_from + operations_from + retrieval
    fees_dataframes = []
    for location in LOCATIONS:
        archive_fees_network = network[US]  # Cost to archive from Terra (multi regional)
        retrieval_fees_network = network[location]  # Cost to retrieve from location
        for storage_type in STORAGE_TYPES:
            archive_fees_a_operations = a_operations[storage_type]  # Cost to archive to new storage type
            retrieval_fees_a_operations = a_operations[STANDARD]  # Cost to retrieve to Terra (standard)
            retrieval_fees_retrieval = retrieval[storage_type]   # Cost for retrieval

            archive_total = archive_fees_network + archive_fees_a_operations
            retrieval_total = retrieval_fees_network + retrieval_fees_a_operations + retrieval_fees_retrieval

            series = pd.Series(0)
            series.loc['archive_fee_network'] = archive_fees_network
            series.loc['archive_fee_class_a_operations'] = archive_fees_a_operations
            series.loc['retrieval_fee_network'] = retrieval_fees_network
            series.loc['retrieval_fee_class_a_operations'] = retrieval_fees_a_operations
            series.loc['retrieval_fee_retrieval'] = retrieval_fees_retrieval
            series.loc['archive_fee_total'] = archive_total
            series.loc['retrieval_fee_total'] = retrieval_total
            series.loc['fees_total'] = archive_total + retrieval_total
            if location == US and storage_type == STANDARD:
                series.loc[:] = 0
            series.loc['location'] = location
            series.loc['storage_type'] = storage_type
            fees_dataframes.append(series.to_frame().T.set_index(['location', 'storage_type']))
    return pd.concat(fees_dataframes).iloc[:, 1:]


def calculate_network_charges(usage_gigabytes):
    # NETWORK CHARGES: https://cloud.google.com/storage/pricing#network-pricing
    return {
        US: NETWORK[US] * usage_gigabytes,
        US_CENTRAL: NETWORK[US_CENTRAL] * usage_gigabytes
    }


def calculate_operations_charges(number_of_files, operations_cost_dictionary):
    # https://cloud.google.com/storage/pricing#operations-pricing
    # Class A operations are charged at the rate associated with the object's _destination_ storage class
    dictionary = {}
    for storage_type in STORAGE_TYPES:
        dictionary[storage_type] = number_of_files * operations_cost_dictionary[storage_type] / 10000
    return dictionary


def calculate_retrieval_charges(usage_gigabytes):
    # https://cloud.google.com/storage/pricing#archival-pricing
    dictionary = {}
    for storage_type in STORAGE_TYPES:
        dictionary[storage_type] = RETRIEVAL_COST[storage_type] * usage_gigabytes
    return dictionary


def calculate_storage_charges(usage_gigabytes):
    costs = []
    for location in LOCATIONS:
        for storage_type in STORAGE_TYPES:
            costs.append((location, storage_type, STORAGE_COSTS[location][storage_type] * usage_gigabytes))
    return costs


def calculate_storage_charges_over_time(time_scale, storage):
    assert time_scale in ['day', 'month'], 'time_scale must be day or month'
    divisor = 30 if time_scale == 'day' else 1
    duration = 550 if time_scale == 'day' else 19
    unit_label_column = f'{time_scale} storage cost'
    units = list(range(1, duration + 1))

    df = pd.DataFrame(storage, columns=['location', 'storage_type', unit_label_column])
    if time_scale == 'day':
        df.loc[df.index, unit_label_column] = df.loc[df.index, unit_label_column] / divisor
    df.set_index(['location', 'storage_type'], inplace=True)

    costs = pd.DataFrame(0, index=df.index, columns=units)
    for location in LOCATIONS:
        for storage_type in STORAGE_TYPES:
            multiple = df.loc[(location, storage_type), unit_label_column]
            costs.loc[(location, storage_type), units] = [unit * multiple for unit in units]
    return pd.concat([df, costs], axis=1)


def create_page_information(dictionary, n_blobs, n_blobs_no_logs):
    series = pd.Series(dictionary)
    series.loc['number of files'] = n_blobs
    series.loc['number of files, no logs'] = n_blobs_no_logs
    return series


def create_page_network_costs(dictionary):
    return pd.Series(dictionary)


def create_page_operations_costs(dictionary_logs, dictionary_no_logs, n, n_no_logs):
    df = pd.DataFrame([dictionary_logs, dictionary_no_logs])
    df['number of files'] = [n, n_no_logs]
    df.index = ['class a operation costs, with logs', 'class a operation costs, without logs']
    return df


def create_page_recommendations(dataframe):
    recommendations = []
    dataframe.columns = [str(column) for column in dataframe.columns]
    for day in ['7', '15', '30', '45', '60', '90', '180', '360', '540']:
        location, storage_type, cumulative_cost = extract_recommendation(dataframe, day)
        terra_cost = dataframe.loc[(US, STANDARD), day]
        savings = cumulative_cost - terra_cost
        dictionary = {'days archived': day,
                      'location': location,
                      'storage type': storage_type,
                      'cumulative cost in recommended storage': cumulative_cost,
                      'cumulative cost in Terra': terra_cost,
                      'cost difference relative to Terra': savings
                      }
        recommendations.append(dictionary)
    return pd.DataFrame(recommendations)


def create_page_retrieval_costs(dictionary):
    return pd.Series(dictionary)


def create_page_storage_costs(groups):
    df = pd.DataFrame(groups, columns=['location', 'storage type', 'monthly cost'])
    df['daily cost'] = df['monthly cost'].divide(30)
    return df


def extract_recommendation(df, day):
    series = df.loc[:, day]
    return series.idxmin()[0], series.idxmin()[1], series.min()


def index_bucket(bucket_name):
    blobs = index_workspace.glob_bucket(bucket_name)
    blobs_no_logs = index_workspace.remove_logs_from_blobs(blobs)
    return blobs, blobs_no_logs


def request_workspace(namespace, name):
    headers = index_workspace.generate_header()
    requested_workspace = index_workspace.get_workspace(namespace, name, headers)
    check_r = index_workspace.check_request(requested_workspace, 'Failed to get workspace')
    if check_r['message'] != 'success!':
        return index_workspace.print_json(check_r)

    bucket_name = requested_workspace.json()['workspace']['bucketName']
    request_usage = index_workspace.get_bucket_usage(namespace, name, headers)
    check_r = index_workspace.check_request(request_usage, 'Failed to get workspace bucket usage')
    if check_r['message'] != 'success!':
        return index_workspace.print_json(check_r)

    usage_bytes = index_workspace.format_usage(request_usage)
    usage_gigabytes, usage_terabytes, monthly_cost = index_workspace.calculate_usage(usage_bytes)
    return {
        'namespace': namespace,
        'name': name,
        'bucket_name': bucket_name,
        'usage_gigabytes': usage_gigabytes,
        'monthly_cost': monthly_cost
    }


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog='Estimate cost of archiving and retrieving Terra workspace',
                                         description="Estimates cost of changing storage classes.")
    arg_parser.add_argument('--namespace', required=True,
                            help='Workspace namespace')
    arg_parser.add_argument('--name', required=True,
                            help='Workspace name')
    args = arg_parser.parse_args()

    input_namespace = args.namespace
    input_name = args.name

    workspace = request_workspace(input_namespace, input_name)
    storage_costs = calculate_storage_charges(workspace['usage_gigabytes'])
    network_costs = calculate_network_charges(workspace['usage_gigabytes'])
    retrieval_costs = calculate_retrieval_charges(workspace['usage_gigabytes'])

    storage_costs_monthly = calculate_storage_charges_over_time('month', storage_costs)
    storage_costs_daily = calculate_storage_charges_over_time('day', storage_costs)

    blobs, blobs_no_logs = index_bucket(workspace['bucket_name'])
    class_a_operation_costs = calculate_operations_charges(len(blobs), OPERATION_A_COST)
    class_a_operation_costs_no_logs = calculate_operations_charges(len(blobs_no_logs), OPERATION_A_COST)
    fees = calculate_fees(network_costs, class_a_operation_costs, retrieval_costs)

    # Adjust daily storage prices for minimum storage duration and then also add fees of archiving and retrieval
    storage_costs_daily_min_duration = adjust_daily_storage_charge(storage_costs_daily)
    storage_costs_daily_with_fees = adjust_storage_charge_fees('day', storage_costs_daily_min_duration, fees)

    print(workspace)
    print(storage_costs)
    print(network_costs)
    print(retrieval_costs)
    print(len(blobs), class_a_operation_costs)
    print(len(blobs_no_logs), class_a_operation_costs_no_logs)
#    print(fees)

    page_information = create_page_information(workspace, len(blobs), len(blobs_no_logs))
    page_recommendations = create_page_recommendations(storage_costs_daily_with_fees)
    page_storage = create_page_storage_costs(storage_costs)
    page_network = create_page_network_costs(network_costs)
    page_retrieval = create_page_retrieval_costs(retrieval_costs)
    page_class_a_operations = create_page_operations_costs(class_a_operation_costs,
                                                           class_a_operation_costs_no_logs,
                                                           len(blobs),
                                                           len(blobs_no_logs)
                                                           )
    page_fees = fees.copy(deep=True)

    output_name = f'{input_namespace}.{input_name}.cost-estimates'
    with pd.ExcelWriter(f'{output_name}.xlsx') as writer:
        page_information.to_excel(writer, sheet_name='Workspace information', header=False)
        page_recommendations.to_excel(writer, sheet_name='Recommendations', index=False)
        page_storage.to_excel(writer, sheet_name='Storage costs', index=False)
        page_network.to_excel(writer, sheet_name='Network costs', header=False)
        page_retrieval.to_excel(writer, sheet_name='Retrieval costs', header=False)
        page_class_a_operations.to_excel(writer, sheet_name='Class A operations gsutil cp')
        page_fees.to_excel(writer, sheet_name='Fees')
        storage_costs_monthly.to_excel(writer, sheet_name='monthly storage cost')
        storage_costs_daily.to_excel(writer, sheet_name='daily storage cost')
        storage_costs_daily_min_duration.to_excel(writer, sheet_name='daily, adj. min duration')
        storage_costs_daily_with_fees.to_excel(writer, sheet_name='daily adj min duration w fees')

    # I can imagine this perhaps being better suited to a flask report with an inline plot of cumulative cost
