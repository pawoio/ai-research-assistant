variable "project_id" {
  type        = string
  description = "The Google Cloud project ID."
}

variable "gcp_apis" {
  type        = list(string)
  description = "A list of Google Cloud APIs to enable on the project."
}
