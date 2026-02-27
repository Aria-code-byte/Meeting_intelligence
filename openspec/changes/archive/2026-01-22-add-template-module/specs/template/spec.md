## ADDED Requirements

### Requirement: User Template Definition

The system SHALL provide a UserTemplate structure for defining how users want to experience meetings.

#### Scenario: Template creation with required fields

- **WHEN** a new template is created
- **THEN** the system requires the following fields:
  - `name`: Unique template identifier
  - `role`: User role (e.g., "Product Manager", "Developer")
  - `angle`: Summary angle (e.g., "towards-conclusions", "towards-process", "towards-decisions")
  - `focus`: List of focus areas (e.g., ["requirements", "decisions", "action-items"])
- **AND** validates that all required fields are present

#### Scenario: Template with optional metadata

- **WHEN** a template is created with optional fields
- **THEN** the system accepts:
  - `description`: Template description
  - `version`: Template version number
  - `sections`: Custom section definitions
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

#### Scenario: Invalid template structure

- **WHEN** a template is created missing required fields
- **THEN** the system raises a clear error
- **AND** indicates which field is missing

---

### Requirement: Template Section Definition

The system SHALL support defining custom sections within templates.

#### Scenario: Section with prompt template

- **WHEN** a section is defined
- **THEN** the system requires:
  - `id`: Unique section identifier
  - `title`: Display title
  - `prompt`: Prompt template for LLM
- **AND** the prompt template supports placeholders

#### Scenario: Section with options

- **WHEN** a section includes configuration options
- **THEN** the system accepts:
  - `required`: Whether section is required
  - `max_length`: Maximum output length
  - `format`: Output format (bullet-points, paragraph, table)

#### Scenario: Section placeholder substitution

- **WHEN** a section prompt contains placeholders
- **THEN** the system supports:
  - `{meeting_title}`: Meeting title placeholder
  - `{duration}`: Meeting duration placeholder
  - `{participant_count}`: Participant count placeholder
  - `{focus_areas}`: Focus areas placeholder

---

### Requirement: Default Template Library

The system SHALL provide a set of pre-configured default templates.

#### Scenario: Product Manager template

- **WHEN** the Product Manager template is requested
- **THEN** the system provides a template with:
  - `role`: "Product Manager"
  - `focus`: ["requirements", "features", "decisions", "action-items", "risks"]
  - `angle`: "towards-conclusions"
  - Sections for: Requirements Summary, Feature Decisions, Action Items, Risks

#### Scenario: Developer template

- **WHEN** the Developer template is requested
- **THEN** the system provides a template with:
  - `role`: "Developer"
  - `focus`: ["technical-decisions", "implementation", "architecture", "bugs"]
  - `angle`: "towards-process"
  - Sections for: Technical Discussion, Implementation Notes, Architecture Decisions

#### Scenario: Designer template

- **WHEN** the Designer template is requested
- **THEN** the system provides a template with:
  - `role`: "Designer"
  - `focus`: ["ux", "user-feedback", "design-decisions", "visuals"]
  - `angle`: "towards-user-impact"
  - Sections for: User Feedback, Design Decisions, UX Considerations

#### Scenario: Executive template

- **WHEN** the Executive template is requested
- **THEN** the system provides a template with:
  - `role`: "Executive"
  - `focus`: ["strategy", "resources", "timeline", "decisions", "roi"]
  - `angle`: "towards-decisions"
  - Sections for: Executive Summary, Key Decisions, Resource Requirements

#### Scenario: General template (fallback)

- **WHEN** no specific template is requested
- **THEN** the system provides a General template with:
  - `role`: "General"
  - `focus`: ["summary", "key-points", "action-items"]
  - `angle`: "balanced"

---

### Requirement: Template Validation

The system SHALL validate templates before use.

#### Scenario: Valid template passes validation

- **WHEN** a well-formed template is validated
- **THEN** the system returns success
- **AND** indicates the template is ready to use

#### Scenario: Template with missing required field

- **WHEN** a template missing a required field is validated
- **THEN** the system returns validation failure
- **AND** indicates which field is missing
- **AND** suggests corrective action

#### Scenario: Template with invalid focus area

- **WHEN** a template contains an unrecognized focus area
- **THEN** the system returns a warning
- **AND** continues with validation (focus areas are extensible)

#### Scenario: Template with duplicate section IDs

- **WHEN** a template has duplicate section IDs
- **THEN** the system returns validation failure
- **AND** indicates the duplicate ID

---

### Requirement: Template Storage

The system SHALL save and load templates from disk.

#### Scenario: Template file creation

- **WHEN** a template is saved
- **THEN** the system creates a JSON file in `data/templates/`
- **AND** the filename matches the template name
- **AND** the file contains the complete template data

#### Scenario: Template file loading

- **WHEN** a template file is loaded
- **THEN** the system reads the JSON file
- **AND** validates the structure
- **AND** returns a UserTemplate object

#### Scenario: Default template initialization

- **WHEN** the system is first initialized
- **THEN** the system creates default templates
- **AND** saves them to `data/templates/`
- **AND** does not overwrite existing custom templates

#### Scenario: Template listing

- **WHEN** all templates are listed
- **THEN** the system returns metadata for each template
- **AND** includes: name, role, description, created_at, is_default

---

### Requirement: Template Management

The system SHALL provide CRUD operations for templates.

#### Scenario: Get template by name

- **WHEN** a template is requested by name
- **THEN** the system returns the template
- **AND** raises an error if not found

#### Scenario: List all templates

- **WHEN** all templates are requested
- **THEN** the system returns a list of template metadata
- **AND** separates default templates from custom templates

#### Scenario: Create custom template

- **WHEN** a new custom template is created
- **AND** passes validation
- **THEN** the system saves it to disk
- **AND** marks it as custom (not default)

#### Scenario: Update existing template

- **WHEN** a custom template is updated
- **THEN** the system validates the changes
- **AND** updates the file on disk
- **AND** updates the `updated_at` timestamp

#### Scenario: Delete custom template

- **WHEN** a custom template is deleted
- **THEN** the system removes the file
- **AND** returns success
- **AND** prevents deletion of default templates

---

### Requirement: Template Rendering to Prompt

The system SHALL convert templates to LLM prompts.

#### Scenario: Render template to prompt

- **WHEN** a template is rendered for LLM
- **THEN** the system generates a structured prompt
- **AND** includes role definition
- **AND** includes focus areas
- **AND** includes section prompts
- **AND** includes placeholder values

#### Scenario: Render with transcript context

- **WHEN** a template is rendered with a transcript
- **THEN** the system includes:
  - Meeting duration
  - Participant count (if available)
  - Focus areas from template
  - Context from transcript

#### Scenario: Render section prompts

- **WHEN** a template with sections is rendered
- **THEN** the system generates prompts for each section
- **AND** maintains section order
- **AND** applies section formatting options

#### Scenario: Render with custom parameters

- **WHEN** a template is rendered with custom parameters
- **THEN** the system substitutes placeholders with provided values
- **AND** handles missing placeholders gracefully
