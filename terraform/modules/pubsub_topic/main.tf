resource "google_pubsub_topic" "topic" {
  name    = var.topic_name
  project = var.project_id

  # Ensure the Pub/Sub API is enabled before trying to create a topic.
  depends_on = [
    var.service_account_apis
  ]
}
