locals {
  create_tables_sql = templatefile("${path.module}/../../sql/001_create_tables.sql", {
    project_id = var.project_id
    dataset_id = var.dataset_id
  })
}

resource "null_resource" "create_bigquery_tables" {
  provisioner "local-exec" {
    command = <<EOT
    bq query \
      --project_id=${var.project_id} \
      --location=${var.location} \
      --nouse_legacy_sql \
      --format=none \
      '${replace(local.create_tables_sql, "'", "'\"'\"'")}'
    EOT
  }
}

# locals {
#   create_index_sql = templatefile("${path.module}/../../sql/002_create_vector_index.sql", {
#     project_id = var.project_id
#     dataset_id = var.dataset_id
#   })
# }

# resource "null_resource" "create_vector_index" {
#   provisioner "local-exec" {
#     command = <<EOT
#     bq query \
#       --project_id=${var.project_id} \
#       --location=${var.location} \
#       --nouse_legacy_sql \
#       --format=none \
#       '${replace(local.create_index_sql, "'", "'\"'\"'")}'
#     EOT
#   }

#   depends_on = [null_resource.create_bigquery_table]
# }
