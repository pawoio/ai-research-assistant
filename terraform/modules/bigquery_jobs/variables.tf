variable "project_id" {
  type        = string
  description = "The Google Cloud project ID."
}

variable "location" {
  type        = string
  description = "The region where the BigQuery jobs will run."
}

variable "dataset_id" {
  type        = string
  description = "The ID of the BigQuery dataset to run jobs against."
}
