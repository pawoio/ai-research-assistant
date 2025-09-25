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

CREATE TABLE IF NOT EXISTS `${project_id}.${dataset_id}.paper_analysis` (
  analysis_id STRING NOT NULL,
  paper_id STRING NOT NULL,
  relevance_score FLOAT64,
  technical_contribution STRING,
  business_impact STRING,
  research_gaps STRING,
  implementation_complexity STRING,
  confidence_scores STRUCT<
    relevance FLOAT64,
    technical FLOAT64,
    business FLOAT64
  >,
  analysis_timestamp TIMESTAMP NOT NULL
);

-- Weekly reports metadata
CREATE TABLE IF NOT EXISTS `${project_id}.${dataset_id}.reports` (
  report_id STRING NOT NULL,
  week_start_date DATE,
  papers_analyzed INT64,
  top_trends ARRAY<STRING>,
  report_content STRING,
  generated_at TIMESTAMP NOT NULL
);