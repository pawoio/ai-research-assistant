CREATE TABLE IF NOT EXISTS `${project_id}.${dataset_id}.papers` (
  paper_id STRING NOT NULL,
  title STRING NOT NULL,
  abstract STRING,
  authors ARRAY<STRING>,
  publication_date DATE,
  venue STRING,
  embedding ARRAY<FLOAT64>,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(created_at)
CLUSTER BY venue, publication_date
;
