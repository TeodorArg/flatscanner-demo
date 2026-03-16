# Tasks: Claude Review Status Alias Support

## Spec

- [x] Record the observed `review_status` payload shape
- [x] Keep the Claude review contract strict while allowing compatible status aliases

## Documentation

- [x] Update operator docs to mention `review_status` normalization

## Workflow And Scripts

- [x] Normalize `review_status` to `verdict` in the Claude parser
- [x] Add regression coverage for the observed `review_status` shape

## Validation

- [x] Parse the updated PowerShell scripts successfully
- [x] Run the Claude review output parsing validation script successfully
