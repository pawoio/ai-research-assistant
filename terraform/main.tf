# Enable the foundational API first, as other resources depend on it.
resource "google_project_service" "cloud_resource_manager" {
  project              = var.project_id
  service              = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}

locals {
  gcp_apis = toset([
    "aiplatform.googleapis.com",
    "cloudscheduler.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com"
  ])
}

# Enable the rest of the required APIs
resource "google_project_service" "required_apis" {
  for_each = local.gcp_apis

  project              = var.project_id
  service              = each.value
  disable_on_destroy = false

  # Explicitly depend on the foundational API to ensure correct creation order.
  depends_on = [google_project_service.cloud_resource_manager]
}

# BigQuery datasets for research data
resource "google_bigquery_dataset" "research_data" {
  dataset_id = var.bigquery_dataset_id
  project    = var.project_id
  location   = var.region

  description = "Research papers and analysis data"
}

# Cloud Storage bucket for research papers
resource "google_storage_bucket" "paper_storage" {
  name     = var.gcs_bucket_name
  project  = var.project_id
  location = var.region

  lifecycle_rule {
    condition {
      age = var.gcs_lifecycle_age_days
    }
    action {
      type = "Delete"
    }
  }
}

# Pub/Sub topic for pipeline orchestration
resource "google_pubsub_topic" "pipeline_triggers" {
  name    = var.pubsub_topic_name
  project = var.project_id
}


locals {
  create_tables_sql = templatefile("${path.module}/sql/001_create_tables.sql", {
    project_id = var.project_id
    dataset_id = google_bigquery_dataset.research_data.dataset_id
  })
}

resource "google_bigquery_job" "create_tables" {
  job_id   = "create_tables_${replace(timestamp(), ":", "_")}"
  location = var.region

  query {
    query          = local.create_tables_sql
    use_legacy_sql = false
  }

  depends_on = [google_bigquery_dataset.research_data]
}

locals {
  create_index_sql = templatefile("${path.module}/sql/002_create_vector_index.sql", {
    project_id = var.project_id
    dataset_id = google_bigquery_dataset.research_data.dataset_id
  })
}

resource "google_bigquery_job" "create_vector_index" {
  job_id   = "create_vector_index_${replace(timestamp(), ":", "_")}"
  location = var.region

  query {
    query          = local.create_index_sql
    use_legacy_sql = false
  }

  depends_on = [google_bigquery_job.create_tables]
}