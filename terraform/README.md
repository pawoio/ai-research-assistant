# Terraform Configuration for AI Research Assistant

This folder contains the Terraform configuration for managing Google Cloud resources for the AI Research Assistant project.

## Structure

- **main.tf**: Entry point for Terraform, orchestrates modules and shared resources.
- **variables.tf**: Defines input variables for the project.
- **outputs.tf**: Outputs from the Terraform configuration.
- **provider.tf**: Configures the Google Cloud provider.
- **terraform.tfvars**: Contains values for input variables (not included in version control).
- **modules/**: Contains reusable Terraform modules for specific resources.
  - **bigquery_dataset/**: Manages BigQuery datasets.
  - **bigquery_jobs/**: Manages BigQuery jobs (e.g., SQL execution).
  - **project_apis/**: Enables required Google Cloud APIs.
  - **pubsub_topic/**: Manages Pub/Sub topics.
  - **storage_bucket/**: Manages Cloud Storage buckets.
- **sql/**: Contains SQL files for BigQuery jobs.

## Usage

1. **Initialize Terraform**:
   Initializes the working directory, downloading providers and modules. This is the first command you should run.

   ```bash
   terraform init
   ```

2. **Validate Terraform Configuration**:
   Checks if the configuration is syntactically valid and internally consistent. It's a good practice to run this before planning.

   ```bash
   terraform validate
   ```

3. **Plan Terraform Changes**:
   Creates an execution plan, showing what changes will be made to your infrastructure. **Always review the plan before applying.**

   ```bash
   terraform plan
   ```

4. **Apply Terraform Configuration**:
   Applies the changes defined in your configuration to create, update, or delete resources.

   ```bash
   terraform apply
   ```

5. **Destroy Resources (Optional)**:
   Destroys all resources managed by this Terraform configuration. Use with caution.

   ```bash
   terraform destroy
   ```
