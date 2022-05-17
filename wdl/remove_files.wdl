version 1.0


workflow remove_files_workflow {
    meta {
        description: "Removes files successfully copied from gsutil cp, see https://github.com/vanallenlab/terra-helper"
    }

    input {
        String source_namespace
        String source_name
        String source_bucket
        String destination_namespace
        String destination_name
        String destination_bucket
        File gsutil_copy_log
        Int memoryGB

        String source = sub(source_bucket, "gs://", "")
        String destination = sub(destination_bucket, "gs://", "")
    }

    call remove_files {
        input:
            gsutil_copy_log = gsutil_copy_log,
            source_bucket = source,
            destination_bucket = destination,
            memoryGB = memoryGB
    }

    output {
        File removed_files = remove_files.removed_files
    }
}

task remove_files {
    input {
        File gsutil_copy_log
        String source_bucket
        String destination_bucket
        Int memoryGB
    }

    command {
        python /list_source_files.py --input ~{gsutil_copy_log} --output ~{source_bucket}

        bash /remove_files.sh "~{source_bucket}.files_to_remove.txt"

        gsutil cp "~{source_bucket}.files_to_remove.txt" "gs://~{source_bucket}"
        gsutil cp "~{source_bucket}.files_to_remove.txt" "gs://~{destination_bucket}"
    }

    output {
        File removed_files = "~{source_bucket}.files_to_remove.txt"
    }

    runtime {
        docker: "vanallenlab/terra-helper:1.0.0"
        memory: "~{memoryGB} GB"
        disks: "local-disk 50 HDD"
    }
}