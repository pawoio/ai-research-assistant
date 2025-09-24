CREATE TABLE IF NOT EXISTS `${project_id}.${dataset_id}.papers_vec` (
  paper_id STRING NOT NULL,
  title STRING NOT NULL,
  abstract STRING,
  authors ARRAY<STRING>,
  publication_date DATE,
  venue STRING,
  embedding VECTOR<FLOAT64>(768),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY venue, publication_date;