variable "project_id" {
  type        = string
  description = "Google Cloud project ID"
}

variable "region" {
  type        = string
  description = "Region to deploy resources"
}

variable "bigquery_dataset_id" {
  type        = string
  description = "The ID for the BigQuery dataset."
  default     = "ai_research_assistant"
}

variable "gcs_bucket_name" {
  type        = string
  description = "The globally unique name for the GCS bucket."
  default     = "ai-research-assistant-papers" # Consider making this unique, e.g., "${var.project_id}-research-papers"
}

variable "gcs_lifecycle_age_days" {
  type        = number
  description = "Number of days after which objects in the GCS bucket will be deleted."
  default     = 90
}

variable "pubsub_topic_name" {
  type        = string
  description = "The name for the Pub/Sub topic."
  default     = "research-pipeline-triggers"
}

variable "gcp_apis" {
  type        = list(string)
  description = "A list of Google Cloud APIs to enable on the project."
  default = [
    "aiplatform.googleapis.com",
    "cloudscheduler.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com"
  ]
}