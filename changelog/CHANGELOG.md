# Changelog

All notable changes to CareerHub are documented in this file.

This project follows the principles of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic versioning for release labels.

## [Unreleased]

### Planned

- Complete final responsive review across desktop, tablet, and mobile layouts.
- Validate the generated site through the GitHub Pages deployment workflow.
- Add final accessibility and metadata checks before the first stable release.

## [1.0.0] - 2026-09-21

### Added

- Introduced a YAML-driven portfolio architecture with separate data files for profile, experience, skills, achievements, projects, certifications, and education.
- Added Jinja2 template rendering through `scripts/generate-website.py`.
- Added PyYAML-based loading and validation for all required data files.
- Added automatic generation of `docs/index.html` for GitHub Pages publishing.
- Added recursive copying of the source `assets/` directory into `docs/assets/`.
- Added UTF-8 file handling for YAML input and generated HTML output.
- Added a modern responsive website template with a white and dark theme, orange accent, sticky navigation, and mobile navigation.
- Added a theme preference switcher backed by browser local storage.
- Added responsive reveal animations with reduced-motion support.
- Added a Career Pathway experience design that alternates left and right on desktop and becomes a vertical timeline on mobile.
- Added YAML-driven experience periods with automatic `Present` handling for the current role.
- Added YAML-driven sections for expertise, selected achievements, projects, about information, education, professional development, and contact links.
- Added featured-project support and a primary-feature presentation flag for the main personal project card.
- Added image-based project visuals with icon fallbacks for projects without a configured image.
- Added project icon mapping for Python Build and Validation Automation, Selenium Operational Automation, CareerHub, and the primary personal project.
- Added support for optional project outcome and public URL fields.
- Added support for rendering project technologies, capabilities, vision, and status from YAML.
- Added validation for required YAML files, top-level keys, profile assets, project assets, and safe relative asset paths.
- Added strict Jinja2 undefined-variable checks to expose template and data mismatches during generation.
- Added clear success and error messages for the website generation process.

### Changed

- Repositioned the website as a professional CareerHub portfolio rather than a resume-style page.
- Replaced the tabular experience presentation with a visual Career Pathway.
- Updated the experience sequence to present the current Disney Travel Box engagement first, followed by BMW Purchasing, BMW Quality, and Infosys BPM experience.
- Updated project rendering so featured status is controlled by YAML rather than hardcoded HTML.
- Updated the Projects and Automation section to show only projects marked as featured.
- Updated the main personal project visual from a full dashboard screenshot to a compact project logo for improved layout balance.
- Updated the main project card to use YAML-driven descriptive content and capabilities instead of leaving unused visual space.
- Updated project image styling to use a contained, centered visual rather than a full-card cover image.
- Updated the generator to prepare display-only metadata without modifying YAML source files.
- Updated experience and skill ordering to respect priority and display-order values from YAML.
- Updated the template to consume the generator-provided `role.period`, `project.visual`, and `project.is_primary_feature` values.
- Updated optional project-field checks to remain compatible with strict Jinja2 validation.
- Updated the hero heading to render the complete profile name directly from YAML.
- Updated project cards to use consistent visual treatment for image and icon content.

### Fixed

- Fixed the missing `project_initials` Jinja2 filter error by removing the obsolete template dependency.
- Fixed project visuals that previously rendered image paths as plain text.
- Fixed project images not being copied to the generated GitHub Pages asset directory.
- Fixed oversized project images by applying constrained width, height, and `object-fit: contain` styling.
- Fixed the main project card layout that created excessive unused space beneath its content.
- Fixed the `dict object has no attribute outcome` generation error by safely checking optional YAML fields.
- Fixed the `.project-mark` CSS selector after the class prefix was omitted.
- Fixed duplicated project visual markup and an extra Jinja2 `{% endif %}` statement.
- Fixed mismatched closing elements in the project-card structure.
- Fixed brittle project highlighting that depended on loop position instead of the project identifier.
- Fixed unsafe silent rendering of undefined template values by enabling strict validation.
- Fixed date formatting for `YYYY-MM` and `YYYY-MM-DD` YAML values.
- Fixed asset-path handling for both string and mapping forms of `hero_image`.
- Fixed source asset validation so missing profile and project images produce actionable errors.
- Fixed UTF-8 handling required for names containing non-ASCII characters.

### Architecture

- Confirmed YAML files as the single source of truth for all portfolio content.
- Confirmed that the HTML template contains presentation markup and Jinja2 placeholders only.
- Confirmed that no career history, project description, achievement, skill, education, certification, or profile content is duplicated in the generator.
- Confirmed that generated website output is written only to `docs/index.html` with supporting assets under `docs/assets/`.
- Confirmed that CareerHub remains excluded from the featured-project display through its YAML `featured` setting.

## [0.1.0] - 2026-09-18

### Added

- Created the initial CareerHub repository structure.
- Added folders for structured data, templates, scripts, generated documentation, and static assets.
- Added the initial profile, experience, skills, achievements, projects, certifications, and education YAML files.
- Added the initial website template and GitHub Pages output direction.

[Unreleased]: https://github.com/Deepansri94/Deepan_CareerHub/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Deepansri94/Deepan_CareerHub/releases/tag/v1.0.0
[0.1.0]: https://github.com/Deepansri94/Deepan_CareerHub/releases/tag/v0.1.0
