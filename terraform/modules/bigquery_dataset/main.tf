resource "google_bigquery_dataset" "dataset" {
  dataset_id  = var.dataset_id
  project     = var.project_id
  location    = var.location
  description = "Research papers and analysis data"

  # Ensure the BigQuery API is enabled before trying to create a dataset.
  depends_on = [
    var.service_account_apis
  ]
}
