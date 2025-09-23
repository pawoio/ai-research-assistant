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
  value       = google_bigquery_dataset.research_data.dataset_id
}

output "gcs_bucket_name" {
  description = "The name of the GCS bucket for storing research papers."
  value       = google_storage_bucket.paper_storage.name
}

output "pubsub_topic_name" {
  description = "The name of the Pub/Sub topic for pipeline triggers."
  value       = google_pubsub_topic.pipeline_triggers.name
}