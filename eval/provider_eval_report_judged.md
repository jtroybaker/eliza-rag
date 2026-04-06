# Eval Artifact Report

Artifacts compared: 4

## Run Summary

| Run | Embedder | Reranker | Mode | Include Answer | Answer Judging | Pass | Partial | Fail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| snowflake-arctic-embed-xs + bge-reranker-v2-m3 | snowflake-arctic-embed-xs | bge-reranker-v2-m3 | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 4 | 1 | 1 |
| hashed_v1 + bge-reranker-base | hashed_v1 | bge-reranker-base | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 2 | 2 | 2 |
| hashed_v1 + bge-reranker-v2-m3 | hashed_v1 | bge-reranker-v2-m3 | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 1 | 5 | 0 |
| snowflake-arctic-embed-xs + bge-reranker-base | snowflake-arctic-embed-xs | bge-reranker-base | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 2 | 3 | 1 |

## Query Matrix

| Query | Run | Outcome | Answer Overall | Answer Score | Groundedness | Comparison Completeness |
| --- | --- | --- | --- | --- | --- | --- |
| compare_aapl_tsla_jpm_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | pass | pass | 4.15 | pass | partial_pass |
| compare_aapl_tsla_jpm_risk_factors | hashed_v1 + bge-reranker-base | fail | fail | 0.00 | error | not_applicable |
| compare_aapl_tsla_jpm_risk_factors | hashed_v1 + bge-reranker-v2-m3 | partial_pass | partial_pass | 3.45 | pass | fail |
| compare_aapl_tsla_jpm_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | partial_pass | partial_pass | 3.50 | pass | fail |
| compare_aapl_tsla_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | pass | partial_pass | 3.95 | pass | pass |
| compare_aapl_tsla_risk_factors | hashed_v1 + bge-reranker-base | pass | pass | 4.00 | pass | pass |
| compare_aapl_tsla_risk_factors | hashed_v1 + bge-reranker-v2-m3 | pass | pass | 4.30 | pass | pass |
| compare_aapl_tsla_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | pass | pass | 4.00 | pass | pass |
| compare_jpm_bac_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | pass | pass | 4.15 | pass | partial_pass |
| compare_jpm_bac_risk_factors | hashed_v1 + bge-reranker-base | pass | pass | 4.15 | pass | partial_pass |
| compare_jpm_bac_risk_factors | hashed_v1 + bge-reranker-v2-m3 | partial_pass | partial_pass | 3.65 | pass | partial_pass |
| compare_jpm_bac_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | partial_pass | partial_pass | 3.75 | pass | fail |
| sector_regulatory_banks_capital | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | fail | partial_pass | 3.76 | pass | not_applicable |
| sector_regulatory_banks_capital | hashed_v1 + bge-reranker-base | fail | fail | 0.00 | error | not_applicable |
| sector_regulatory_banks_capital | hashed_v1 + bge-reranker-v2-m3 | partial_pass | partial_pass | 3.71 | pass | not_applicable |
| sector_regulatory_banks_capital | snowflake-arctic-embed-xs + bge-reranker-base | fail | pass | 4.35 | pass | not_applicable |
| single_company_aapl_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | partial_pass | pass | 4.35 | pass | not_applicable |
| single_company_aapl_risk_factors | hashed_v1 + bge-reranker-base | partial_pass | pass | 4.35 | pass | not_applicable |
| single_company_aapl_risk_factors | hashed_v1 + bge-reranker-v2-m3 | partial_pass | pass | 4.29 | pass | not_applicable |
| single_company_aapl_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | partial_pass | pass | 4.29 | pass | not_applicable |
| time_bounded_nvda_revenue_growth | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | pass | pass | 4.41 | pass | not_applicable |
| time_bounded_nvda_revenue_growth | hashed_v1 + bge-reranker-base | partial_pass | pass | 4.35 | pass | not_applicable |
| time_bounded_nvda_revenue_growth | hashed_v1 + bge-reranker-v2-m3 | partial_pass | pass | 4.35 | pass | not_applicable |
| time_bounded_nvda_revenue_growth | snowflake-arctic-embed-xs + bge-reranker-base | pass | pass | 4.35 | pass | not_applicable |

## Failure Clusters

- `compare_aapl_tsla_jpm_risk_factors`: hashed_v1 + bge-reranker-base (fail), hashed_v1 + bge-reranker-v2-m3 (partial_pass), snowflake-arctic-embed-xs + bge-reranker-base (partial_pass)
- `compare_jpm_bac_risk_factors`: hashed_v1 + bge-reranker-v2-m3 (partial_pass), snowflake-arctic-embed-xs + bge-reranker-base (partial_pass)
- `sector_regulatory_banks_capital`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (fail), hashed_v1 + bge-reranker-base (fail), hashed_v1 + bge-reranker-v2-m3 (partial_pass), snowflake-arctic-embed-xs + bge-reranker-base (fail)
- `single_company_aapl_risk_factors`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (partial_pass), hashed_v1 + bge-reranker-base (partial_pass), hashed_v1 + bge-reranker-v2-m3 (partial_pass), snowflake-arctic-embed-xs + bge-reranker-base (partial_pass)
- `time_bounded_nvda_revenue_growth`: hashed_v1 + bge-reranker-base (partial_pass), hashed_v1 + bge-reranker-v2-m3 (partial_pass)
