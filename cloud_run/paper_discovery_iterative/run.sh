gcloud run deploy paper-discovery \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1

SERVICE_URL=$(gcloud run services describe paper-discovery --region europe-west1 --format 'value(status.url)')