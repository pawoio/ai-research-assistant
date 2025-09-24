# Enable the foundational API first, as other resources depend on it.
resource "google_project_service" "cloud_resource_manager" {
  project            = var.project_id
  service            = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}

# Enable the rest of the required APIs
resource "google_project_service" "required_apis" {
  # Convert the list to a set to ensure no duplicates and for use in for_each
  for_each = toset(var.gcp_apis)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false

  # Explicitly depend on the foundational API to ensure correct creation order.
  # This prevents race conditions where a service might be enabled before its
  # core dependency is ready.
  depends_on = [
    google_project_service.cloud_resource_manager
  ]
}
