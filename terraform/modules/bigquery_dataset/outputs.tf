output "dataset_id" {
  description = "The ID of the created BigQuery dataset."
  value       = google_bigquery_dataset.dataset.dataset_id
}

output "self_link" {
  description = "The self_link of the created BigQuery dataset."
  value       = google_bigquery_dataset.dataset.self_link
}
