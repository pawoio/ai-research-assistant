locals {
  create_tables_sql = templatefile("${path.module}/../../sql/001_create_tables.sql", {
    project_id = var.project_id
    dataset_id = var.dataset_id
  })
}

resource "google_bigquery_job" "create_tables" {
  job_id   = "create_tables_${replace(timestamp(), ":", "_")}"
  location = var.location
  project  = var.project_id

  query {
    query          = local.create_tables_sql
    use_legacy_sql = false
  }
}

locals {
  create_index_sql = templatefile("${path.module}/../../sql/002_create_vector_index.sql", {
    project_id = var.project_id
    dataset_id = var.dataset_id
  })
}

resource "google_bigquery_job" "create_vector_index" {
  job_id   = "create_vector_index_${replace(timestamp(), ":", "_")}"
  location = var.location
  project  = var.project_id

  query {
    query          = local.create_index_sql
    use_legacy_sql = false
  }

  depends_on = [google_bigquery_job.create_tables]
}
