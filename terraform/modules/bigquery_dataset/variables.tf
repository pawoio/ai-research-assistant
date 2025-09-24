variable "project_id" {
  type        = string
  description = "The Google Cloud project ID."
}

variable "dataset_id" {
  type        = string
  description = "The ID for the BigQuery dataset."
}

variable "location" {
  type        = string
  description = "The region where the dataset will be created."
}

variable "service_account_apis" {
  type        = any
  description = "A list of enabled APIs, used to enforce dependency."
}
