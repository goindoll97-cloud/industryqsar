# Human inhalation hematotoxicity evidence expansion v0.4

This is a compact public index of the v0.4 expansion; the detailed local ZIP contains the full integrated registry, queue audit, reproducible builder and file hashes. v0.3 is unchanged. Human in vivo inhalation only; concentrations and durations unrestricted. Mixed routes, uncertain attribution and non-target evidence remain audit/hold only.

- 33 additional curated source rows (7 prior-citation links, 26 unlinked observation candidates, not independent studies); 11 candidate, 22 hold.
- 12 additional CAS identities, 56 total with v0.3; 147 source rows (114 + 33), including excluded and uncertain records.
- 949 queue rows: 87 previously linked, 55 newly linked, 92 additional manual context dispositions, 715 pending. Automatic flags are not adjudication.
- 2 primary-text positive references: benzene (core hematology), nitrobenzene (functional hemoglobin). Separate endpoints; reference labels are not final binary training labels. No verified negative labels. No independent reviewer sign-off.

## Files
- additional_evidence_index.csv: evidence ID, CAS/name, citation, original source row IDs, PDF URL/page, exposure route/concentration/duration, endpoint, effect, review bucket, limitations, primary URL/access level, prior links, species, blank training label. Notes are condensed relative to the full local archive.
- additional_chemical_identity.csv: candidate structures for 12 new CAS; RDKit parsing in local workflow, no registry verification.
- primary_positive_references.csv: endpoint-specific references, primary article access and caveats.
- metadata.json: audit counts and hashes.

Do not treat candidate and hold rows as positive/negative model labels. Prior overlapping records must not be counted as independent. Source PDF page indices are one-based. Empty means missing/unassigned, not zero. For publication obtain full primary study details, registry confirmation, independent review and finalize labels. No source PDFs or verbatim excerpts included.
