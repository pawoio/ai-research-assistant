output "project_id" {
  description = "The Google Cloud project ID."
  value       = var.project_id
}

output "region" {
  description = "The Google Cloud region where resources are deployed."
  value       = var.region
}

output "bigquery_dataset_id" {
  description = "The ID of the created BigQuery dataset."
  value       = module.bigquery_dataset.dataset_id
}

output "bigquery_dataset_self_link" {
  description = "The self_link of the created BigQuery dataset."
  value       = module.bigquery_dataset.self_link
}

output "gcs_bucket_name" {
  description = "The name of the GCS bucket for storing research papers."
  value       = module.storage_bucket.name
}

output "pubsub_topic_name" {
  description = "The name of the Pub/Sub topic for pipeline triggers."
  value       = module.pubsub_topic.name
}
