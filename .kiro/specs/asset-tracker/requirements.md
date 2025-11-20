# Requirements Document

## Introduction

The Asset Tracker Tool is a system designed to manage IT assets (laptops and desktops) within an organization. The system tracks asset assignments to users, manages asset lifecycle operations (add, free, delete), and maintains detailed records of all assets including their assignment status, user information, and technical specifications.

## Glossary

- **Asset Tracker System**: The software application that manages IT asset inventory and assignments
- **Asset**: A physical IT device (laptop or desktop computer) tracked by the system
- **User**: An employee or staff member to whom an asset may be assigned
- **Team**: A work group within the organization (e.g., Ashitha, Suma, Data Center Team)
- **Serial Number**: A unique manufacturer-assigned identifier for each asset
- **Asset Tag**: An organization-assigned identifier (BIDC number) for tracking purposes
- **System Type**: The category of asset (Laptop or Desktop)
- **IP Address**: The network address assigned to an asset
- **Active Assets Page**: The main interface displaying currently assigned or available assets
- **Free Systems Page**: A separate interface displaying assets that have been released from assignment
- **Add Operation**: The action of registering a new asset or assigning an asset to a user
- **Free Operation**: The action of releasing an asset from a user (typically when staff leaves)
- **Delete Operation**: The action of removing an asset from the system (typically for scrapped systems)

## Requirements

### Requirement 1

**User Story:** As an IT administrator, I want to view all active assets with their complete details on the front page, so that I can quickly see the current asset inventory and assignments.

#### Acceptance Criteria

1. WHEN the Asset Tracker System starts THEN the system SHALL display the Active Assets Page with all non-freed assets
2. WHEN displaying an asset THEN the system SHALL show serial number, user name, team, asset tag, system type, and IP address
3. WHEN the Active Assets Page loads THEN the system SHALL organize assets in a readable tabular format
4. WHEN an asset has no assigned user THEN the system SHALL display the asset with empty user and team fields

### Requirement 2

**User Story:** As an IT administrator, I want to add new assets or assign assets to users, so that I can maintain accurate records of asset allocation.

#### Acceptance Criteria

1. WHEN an administrator clicks the add option for an asset THEN the system SHALL display an input form for asset details
2. WHEN an administrator submits asset details THEN the system SHALL validate that serial number and asset tag are unique
3. WHEN an administrator submits valid asset details THEN the system SHALL create a new asset record and display it on the Active Assets Page
4. WHEN an administrator submits asset details with duplicate serial number or asset tag THEN the system SHALL reject the submission and display an error message
5. WHEN adding an asset THEN the system SHALL require serial number, asset tag, and system type as mandatory fields

### Requirement 3

**User Story:** As an IT administrator, I want to free assets when staff members leave, so that I can track available assets for reassignment.

#### Acceptance Criteria

1. WHEN an administrator clicks the free option for an asset THEN the system SHALL remove the asset from the Active Assets Page
2. WHEN an asset is freed THEN the system SHALL transfer all asset details to the Free Systems Page
3. WHEN an asset is freed THEN the system SHALL preserve all original asset information including serial number, user name, team, asset tag, system type, and IP address
4. WHEN the Free Systems Page is accessed THEN the system SHALL display all freed assets with their complete details
5. WHEN an asset is freed THEN the system SHALL record the operation with a timestamp

### Requirement 4

**User Story:** As an IT administrator, I want to delete assets that are scrapped, so that I can remove obsolete equipment from the tracking system.

#### Acceptance Criteria

1. WHEN an administrator clicks the delete option for an asset THEN the system SHALL prompt for confirmation before deletion
2. WHEN an administrator confirms deletion THEN the system SHALL permanently remove the asset from the Active Assets Page
3. WHEN an asset is deleted THEN the system SHALL not transfer the asset to the Free Systems Page
4. WHEN a deletion is confirmed THEN the system SHALL remove all associated asset data from the active inventory

### Requirement 5

**User Story:** As an IT administrator, I want to access a separate page for freed systems, so that I can view all assets available for reassignment.

#### Acceptance Criteria

1. WHEN the Asset Tracker System runs THEN the system SHALL provide navigation to access the Free Systems Page
2. WHEN the Free Systems Page is accessed THEN the system SHALL display all assets that have been freed
3. WHEN displaying freed assets THEN the system SHALL show the same details as the Active Assets Page (serial number, user name, team, asset tag, system type, IP address)
4. WHEN no assets have been freed THEN the system SHALL display an empty list or appropriate message

### Requirement 6

**User Story:** As an IT administrator, I want the system to persist all asset data, so that information is retained between sessions.

#### Acceptance Criteria

1. WHEN the Asset Tracker System closes THEN the system SHALL save all active asset data to persistent storage
2. WHEN the Asset Tracker System closes THEN the system SHALL save all freed asset data to persistent storage
3. WHEN the Asset Tracker System starts THEN the system SHALL load all previously saved active assets
4. WHEN the Asset Tracker System starts THEN the system SHALL load all previously saved freed assets
5. WHEN data persistence fails THEN the system SHALL display an error message to the administrator

### Requirement 7

**User Story:** As an IT administrator, I want to search and filter assets, so that I can quickly locate specific assets or view assets by team or user.

#### Acceptance Criteria

1. WHEN an administrator enters search criteria THEN the system SHALL filter displayed assets to match the criteria
2. WHEN filtering by asset tag (BIDC number) THEN the system SHALL perform exact or partial matching
3. WHEN filtering by user name THEN the system SHALL display only assets assigned to that user
4. WHEN filtering by team THEN the system SHALL display only assets assigned to that team
5. WHEN search criteria are cleared THEN the system SHALL display all assets again
