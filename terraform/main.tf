module "project_apis" {
  source = "./modules/project_apis"

  project_id = var.project_id
  gcp_apis   = var.gcp_apis
}

module "storage_bucket" {
  source = "./modules/storage_bucket"

  project_id           = var.project_id
  bucket_name          = var.gcs_bucket_name
  location             = var.region
  lifecycle_age_days   = var.gcs_lifecycle_age_days
  service_account_apis = module.project_apis.service_account_apis
}

module "pubsub_topic" {
  source = "./modules/pubsub_topic"

  project_id           = var.project_id
  topic_name           = var.pubsub_topic_name
  service_account_apis = module.project_apis.service_account_apis
}

module "bigquery_dataset" {
  source = "./modules/bigquery_dataset"

  project_id           = var.project_id
  dataset_id           = var.bigquery_dataset_id
  location             = var.region
  service_account_apis = module.project_apis.service_account_apis
}

module "bigquery_jobs" {
  source = "./modules/bigquery_jobs"

  project_id = var.project_id
  location   = var.region
  dataset_id = module.bigquery_dataset.dataset_id

  # Ensure the dataset exists before running jobs against it.
  depends_on = [
    module.bigquery_dataset
  ]
}
