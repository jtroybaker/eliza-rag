# Eval Artifact Report

Artifacts compared: 4

## Run Summary

| Run | Embedder | Reranker | Mode | Include Answer | Answer Judging | Pass | Partial | Fail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| snowflake-arctic-embed-xs + bge-reranker-v2-m3 | snowflake-arctic-embed-xs | bge-reranker-v2-m3 | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 0 | 1 | 5 |
| hashed_v1 + bge-reranker-base | hashed_v1 | bge-reranker-base | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 2 | 2 | 2 |
| hashed_v1 + bge-reranker-v2-m3 | hashed_v1 | bge-reranker-v2-m3 | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 0 | 3 | 3 |
| snowflake-arctic-embed-xs + bge-reranker-base | snowflake-arctic-embed-xs | bge-reranker-base | targeted_hybrid | yes | llm_judge_openrouter_quantitative | 0 | 1 | 5 |

## Query Matrix

| Query | Run | Outcome | Answer Overall | Answer Score | Groundedness | Comparison Completeness |
| --- | --- | --- | --- | --- | --- | --- |
| compare_aapl_tsla_jpm_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | fail | partial_pass | 2.50 | fail | partial_pass |
| compare_aapl_tsla_jpm_risk_factors | hashed_v1 + bge-reranker-base | fail | fail | 0.00 | error | not_applicable |
| compare_aapl_tsla_jpm_risk_factors | hashed_v1 + bge-reranker-v2-m3 | fail | fail | 1.90 | fail | fail |
| compare_aapl_tsla_jpm_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | partial_pass | partial_pass | 3.10 | partial_pass | fail |
| compare_aapl_tsla_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | fail | fail | 2.20 | fail | fail |
| compare_aapl_tsla_risk_factors | hashed_v1 + bge-reranker-base | pass | pass | 4.90 | pass | pass |
| compare_aapl_tsla_risk_factors | hashed_v1 + bge-reranker-v2-m3 | partial_pass | partial_pass | 3.30 | partial_pass | partial_pass |
| compare_aapl_tsla_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | fail | partial_pass | 2.65 | fail | pass |
| compare_jpm_bac_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | fail | partial_pass | 2.65 | partial_pass | fail |
| compare_jpm_bac_risk_factors | hashed_v1 + bge-reranker-base | pass | pass | 4.15 | pass | pass |
| compare_jpm_bac_risk_factors | hashed_v1 + bge-reranker-v2-m3 | fail | fail | 2.35 | fail | fail |
| compare_jpm_bac_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | fail | fail | 2.40 | partial_pass | fail |
| sector_regulatory_banks_capital | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | fail | partial_pass | 3.06 | pass | not_applicable |
| sector_regulatory_banks_capital | hashed_v1 + bge-reranker-base | fail | fail | 0.00 | error | not_applicable |
| sector_regulatory_banks_capital | hashed_v1 + bge-reranker-v2-m3 | fail | partial_pass | 3.06 | pass | not_applicable |
| sector_regulatory_banks_capital | snowflake-arctic-embed-xs + bge-reranker-base | fail | partial_pass | 3.71 | pass | not_applicable |
| single_company_aapl_risk_factors | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | fail | partial_pass | 3.00 | pass | not_applicable |
| single_company_aapl_risk_factors | hashed_v1 + bge-reranker-base | partial_pass | partial_pass | 3.29 | pass | not_applicable |
| single_company_aapl_risk_factors | hashed_v1 + bge-reranker-v2-m3 | partial_pass | partial_pass | 3.65 | pass | not_applicable |
| single_company_aapl_risk_factors | snowflake-arctic-embed-xs + bge-reranker-base | fail | partial_pass | 2.65 | partial_pass | not_applicable |
| time_bounded_nvda_revenue_growth | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | partial_pass | partial_pass | 3.06 | partial_pass | not_applicable |
| time_bounded_nvda_revenue_growth | hashed_v1 + bge-reranker-base | partial_pass | partial_pass | 3.94 | pass | not_applicable |
| time_bounded_nvda_revenue_growth | hashed_v1 + bge-reranker-v2-m3 | partial_pass | partial_pass | 2.94 | partial_pass | not_applicable |
| time_bounded_nvda_revenue_growth | snowflake-arctic-embed-xs + bge-reranker-base | fail | fail | 1.94 | fail | not_applicable |

## Failure Clusters

- `compare_aapl_tsla_jpm_risk_factors`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (fail), hashed_v1 + bge-reranker-base (fail), hashed_v1 + bge-reranker-v2-m3 (fail), snowflake-arctic-embed-xs + bge-reranker-base (partial_pass)
- `compare_aapl_tsla_risk_factors`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (fail), hashed_v1 + bge-reranker-v2-m3 (partial_pass), snowflake-arctic-embed-xs + bge-reranker-base (fail)
- `compare_jpm_bac_risk_factors`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (fail), hashed_v1 + bge-reranker-v2-m3 (fail), snowflake-arctic-embed-xs + bge-reranker-base (fail)
- `sector_regulatory_banks_capital`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (fail), hashed_v1 + bge-reranker-base (fail), hashed_v1 + bge-reranker-v2-m3 (fail), snowflake-arctic-embed-xs + bge-reranker-base (fail)
- `single_company_aapl_risk_factors`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (fail), hashed_v1 + bge-reranker-base (partial_pass), hashed_v1 + bge-reranker-v2-m3 (partial_pass), snowflake-arctic-embed-xs + bge-reranker-base (fail)
- `time_bounded_nvda_revenue_growth`: snowflake-arctic-embed-xs + bge-reranker-v2-m3 (partial_pass), hashed_v1 + bge-reranker-base (partial_pass), hashed_v1 + bge-reranker-v2-m3 (partial_pass), snowflake-arctic-embed-xs + bge-reranker-base (fail)
