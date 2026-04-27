# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.4] - 2026-04-27
### Added
- Added a shared HAR request catalog used by the crawler, expected-results generator, and tests.
- Added a comprehensive request-corpus test suite that validates HAR parsing, webapp target coverage, POST payload preservation, stale replay header removal, and OWASP expected-results coverage.
- Added dry-run and JSON output modes for inspecting generated benchmark requests before replay.

### Changed
- Refactored the crawler to replay validated, de-duplicated benchmark requests by default while keeping duplicate replay available with `--include-duplicates`.
- Refactored expected-results generation to use the same validated request catalog as the crawler.
- Bumped Docker image and WAR artifact references to `1.8.4`.

### Fixed
- Fixed OS command POST 500 HAR entries that targeted non-existent `Case01` through `Case04` resources instead of the existing `Case29` through `Case32` benchmark cases.

## [1.8.3] - 2024-07-26
### Fixed
- All the xss that should have POST now cannot use the GET request.

## [1.8.2] - 2024-07-22
### Fixed
- Issue #5
- Fix LFI POST to GET



## [1.8.1] - 2023-04-01 
### Fixed 
- Issue #2
- Issue #3


## [1.8] - 2022-08-15
### Added
- WAVSEP 1.7 test cases 
- pom.xml to build the environment
- Dockerfile that builds a wavsep image
