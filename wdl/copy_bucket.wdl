version 1.0


workflow copy_bucket_workflow {
    meta {
        description: "Copies one bucket to another. See https://github.com/vanallenlab/terra-helper"
    }

    input {
        String source_namespace
        String source_name
        String source_bucket
        String destination_namespace
        String destination_name
        String destination_bucket
        String namespace_to_charge
        Int boot_disk
        Int disk
        Int memory
        File monitoring_script

        String source = sub(source_bucket, "gs://", "")
        String destination = sub(destination_bucket, "gs://", "")
    }

    call copy_bucket {
        input:
            namespace = namespace_to_charge,
            source = source,
            destination = destination,
            boot_disk = boot_disk,
            disk = disk,
            memory = memory,
            monitoring_script = monitoring_script
    }

    output {
        File gsutil_copy_log = copy_bucket.gsutil_copy_log
    }
}

task copy_bucket {
    input {
        String namespace
        String source
        String destination
        String log_name = "~{source}-to-~{destination}.gsutil_copy_log.csv"
        Int boot_disk
        Int disk
        Int memory
        File monitoring_script
    }

    command {
        chmod u+x ~{monitoring_script}
        ~{monitoring_script} > monitoring.log &

        gsutil -u ~{namespace} -m cp -L ~{log_name} -r gs://~{source} gs://~{destination}

        gsutil cp ~{log_name} gs://~{source}
        gsutil cp ~{log_name} gs://~{destination}
    }

    output {
        File gsutil_copy_log = "~{log_name}"
        File monitoringLog = "monitoring.log"
    }

    runtime {
        docker: "vanallenlab/terra-helper:1.0.0"
        memory: "~{memory} GB"
        disks: "local-disk ~{disk} HDD"
        bootDiskSizeGb: "~{boot_disk}"
    }
}
