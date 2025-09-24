variable "project_id" {
  type        = string
  description = "The Google Cloud project ID."
}

variable "bucket_name" {
  type        = string
  description = "The globally unique name for the GCS bucket."
}

variable "location" {
  type        = string
  description = "The region where the bucket will be created."
}

variable "lifecycle_age_days" {
  type        = number
  description = "Number of days after which objects in the bucket will be deleted."
}

variable "service_account_apis" {
  type        = any
  description = "A list of enabled APIs, used to enforce dependency."
}
