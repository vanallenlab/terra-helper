version 1.0

workflow summarize_copy_log {
    meta {
        description: "Summary gsutil copy log"
    }

    input {
        File gsutil_copy_log
    }

    call generate_summary {
        input:
            gsutil_copy_log = gsutil_copy_log
    }

    output {
        String n_files_attempted = generate_summary.n_files_attempted
        String n_files_transferred = generate_summary.n_files_transferred
        String bytes_attempted = generate_summary.bytes_attempted
        String bytes_transferred = generate_summary.bytes_transferred
        String gigibytes_attempted = generate_summary.gigibytes_attempted
        String gigibytes_transferred = generate_summary.gigibytes_transferred
    }
}


task generate_summary {
    input {
        File gsutil_copy_log
    }

    command {
        python /list_source_files.py -i ~{gsutil_copy_log} -o "output" -f -b
    }

    output {
        String n_files_attempted = read_string("n_files_attempted.txt")
        String n_files_transferred = read_string("n_files_transferred.txt")
        String bytes_attempted = read_string("bytes_attempted.txt")
        String bytes_transferred = read_string("bytes_transferred.txt")
        String gigibytes_attempted = read_string("gigibytes_attempted.txt")
        String gigibytes_transferred = read_string("gigibytes_transferred.txt")
    }

    runtime {
        docker: "vanallenlab/terra-helper:1.0.0"
        memory: "2 GB"
        disks: "local-disk 50 HDD"
    }
}