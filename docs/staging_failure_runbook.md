# Staging Failure Runbook

## Purpose

This runbook defines the response to a failed DA1 contract or staging check. Portfolio examples use synthetic data, but the controls mirror a professional operating model.

## Failure classes

| Failure | Immediate response | Owner decision |
|---|---|---|
| Missing or unexpected column | Stop publication and compare the source change with its contract | Accept and version the interface, or restore the source |
| Invalid type | Quarantine the affected delivery and identify the producing-system change | Correct upstream or document an approved parsing rule |
| Missing required value | Stop the affected source and assess scope by field and delivery | Repair upstream, backfill, or approve a documented exception |
| Duplicate primary key | Retain the latest load in staging and report duplicate volume | Confirm whether duplicates represent valid change capture or a source defect |
| Missing source file | Stop the run and check ingestion status | Restore the delivery or formally waive the source for the run |
| Freshness threshold breach | Warn or fail according to the contract threshold | Restore ingestion and communicate downstream-data impact |

## Response sequence

1. Preserve the failed input and validation message.
2. Stop publication of the affected source and dependent products.
3. Identify the owner from the source contract.
4. Quantify affected rows, fields, and downstream consumers.
5. Decide whether to repair, backfill, version the contract, or reject the delivery.
6. Re-run validation and staging from the unchanged raw input or approved replacement.
7. Record the incident, resolution, and preventive action.

## Change-control rule

A schema change is not accepted merely because downstream code can parse it. The source contract, mapping documentation, tests, ownership, classification, and downstream impact must be updated in the same reviewed change.
