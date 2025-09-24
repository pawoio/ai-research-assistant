resource "google_storage_bucket" "bucket" {
  name     = var.bucket_name
  project  = var.project_id
  location = var.location

  lifecycle_rule {
    condition {
      age = var.lifecycle_age_days
    }
    action {
      type = "Delete"
    }
  }

  # Ensure the storage API is enabled before trying to create a bucket.
  depends_on = [
    var.service_account_apis
  ]
}
