variable "project_id" {
  type        = string
  description = "The Google Cloud project ID."
}

variable "topic_name" {
  type        = string
  description = "The name for the Pub/Sub topic."
}

variable "service_account_apis" {
  type        = any
  description = "A list of enabled APIs, used to enforce dependency."
}
