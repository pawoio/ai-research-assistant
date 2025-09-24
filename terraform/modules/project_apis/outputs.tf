# This output is used to create an explicit dependency chain, ensuring that
# other modules that create resources do not start until all their required
# APIs have been enabled by this module.
output "service_account_apis" {
  value = [for s in google_project_service.required_apis : s.service]
}
