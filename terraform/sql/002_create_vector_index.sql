CREATE VECTOR INDEX IF NOT EXISTS papers_embedding_ivf
ON `${project_id}.${dataset_id}.papers` (embedding)
OPTIONS (
  index_type = 'IVF',
  distance_type = 'COSINE',
  ivf_options = '{"num_lists": 2048}'
);
