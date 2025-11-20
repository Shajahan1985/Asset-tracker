# Asset Tracker Tool - Design Document

## Overview

The Asset Tracker Tool is a desktop application built with Python that provides IT administrators with a graphical interface to manage organizational IT assets (laptops and desktops). The system uses a GUI framework (Tkinter) for the user interface and SQLite for data persistence. The application features two main views: an Active Assets page for currently tracked assets and a Free Systems page for released assets.

## Architecture

The application follows a layered architecture pattern:

1. **Presentation Layer**: Tkinter-based GUI components for user interaction
2. **Business Logic Layer**: Asset management operations (add, free, delete, filter)
3. **Data Access Layer**: SQLite database operations for persistence
4. **Data Model Layer**: Asset entity definitions and validation

The architecture ensures separation of concerns, making the system maintainable and testable.

## Components and Interfaces

### 1. Main Application Window
- **Responsibility**: Application entry point and navigation controller
- **Interface**: 
  - `__init__()`: Initialize the application
  - `show_active_assets()`: Display the Active Assets page
  - `show_free_systems()`: Display the Free Systems page
  - `run()`: Start the application main loop

### 2. Active Assets View
- **Responsibility**: Display and manage active assets
- **Interface**:
  - `display_assets(assets: List[Asset])`: Render asset list in table format
  - `on_add_click()`: Handle add button click
  - `on_free_click(asset_id: str)`: Handle free button click
  - `on_delete_click(asset_id: str)`: Handle delete button click
  - `on_filter_change(filter_criteria: dict)`: Apply filters to asset list

### 3. Free Systems View
- **Responsibility**: Display freed assets
- **Interface**:
  - `display_freed_assets(assets: List[Asset])`: Render freed asset list
  - `refresh()`: Reload freed assets from database

### 4. Asset Manager
- **Responsibility**: Business logic for asset operations
- **Interface**:
  - `add_asset(asset: Asset) -> bool`: Add new asset or update existing
  - `free_asset(asset_id: str) -> bool`: Mark asset as freed
  - `delete_asset(asset_id: str) -> bool`: Remove asset permanently
  - `get_active_assets() -> List[Asset]`: Retrieve all active assets
  - `get_freed_assets() -> List[Asset]`: Retrieve all freed assets
  - `filter_assets(criteria: dict) -> List[Asset]`: Filter assets by criteria
  - `validate_asset(asset: Asset) -> tuple[bool, str]`: Validate asset data

### 5. Database Manager
- **Responsibility**: Data persistence and retrieval
- **Interface**:
  - `initialize_database()`: Create tables if not exist
  - `save_asset(asset: Asset, is_freed: bool)`: Persist asset to database
  - `update_asset_status(asset_id: str, is_freed: bool)`: Update asset status
  - `delete_asset(asset_id: str)`: Remove asset from database
  - `load_active_assets() -> List[Asset]`: Load active assets
  - `load_freed_assets() -> List[Asset]`: Load freed assets
  - `check_duplicate(serial_number: str, asset_tag: str) -> bool`: Check for duplicates

### 6. Add Asset Dialog
- **Responsibility**: Collect new asset information from user
- **Interface**:
  - `show() -> Optional[Asset]`: Display dialog and return asset data
  - `validate_input() -> bool`: Validate form inputs

## Data Models

### Asset Entity
```python
class Asset:
    serial_number: str       # Unique manufacturer identifier
    user_name: str          # Name of assigned user (optional)
    team: str               # Team name (optional)
    asset_tag: str          # BIDC number (unique)
    system_type: str        # "Laptop" or "Desktop"
    ip_address: str         # Network IP address (optional)
    is_freed: bool          # Status flag
    freed_timestamp: Optional[datetime]  # When asset was freed
    created_timestamp: datetime          # When asset was added
```

### Database Schema

**Table: assets**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `serial_number` (TEXT UNIQUE NOT NULL)
- `user_name` (TEXT)
- `team` (TEXT)
- `asset_tag` (TEXT UNIQUE NOT NULL)
- `system_type` (TEXT NOT NULL)
- `ip_address` (TEXT)
- `is_freed` (INTEGER DEFAULT 0)
- `freed_timestamp` (TEXT)
- `created_timestamp` (TEXT NOT NULL)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Asset display completeness
*For any* asset in the system, when displayed in the UI, the rendered output should contain the serial number, user name, team, asset tag, system type, and IP address fields.
**Validates: Requirements 1.2**

### Property 2: Unique identifier validation
*For any* asset submission, if an asset already exists with the same serial number or asset tag, the system should reject the submission and return an error.
**Validates: Requirements 2.2, 2.4**

### Property 3: Valid asset addition
*For any* valid asset (with unique serial number and asset tag, and all mandatory fields present), adding it to the system should result in the asset appearing in the active assets list.
**Validates: Requirements 2.3**

### Property 4: Mandatory field validation
*For any* asset submission missing serial number, asset tag, or system type, the system should reject the submission.
**Validates: Requirements 2.5**

### Property 5: Free operation preserves data and transfers location
*For any* active asset, when freed, the asset should: (1) no longer appear in the active assets list, (2) appear in the freed assets list, (3) retain all original field values (serial number, user name, team, asset tag, system type, IP address), and (4) have a freed_timestamp recorded.
**Validates: Requirements 3.1, 3.2, 3.3, 3.5**

### Property 6: Freed assets display completeness
*For any* set of freed assets in the system, accessing the Free Systems Page should display all freed assets with their complete details.
**Validates: Requirements 3.4, 5.2**

### Property 7: Delete operation complete removal
*For any* asset, when deleted (after confirmation), the asset should: (1) not appear in the active assets list, (2) not appear in the freed assets list, and (3) not be retrievable from the database.
**Validates: Requirements 4.2, 4.3, 4.4**

### Property 8: Display format consistency
*For any* asset, the fields displayed should be identical whether the asset appears on the Active Assets Page or the Free Systems Page.
**Validates: Requirements 5.3**

### Property 9: Active assets persistence round-trip
*For any* set of active assets, saving them to the database and then loading them should result in an equivalent set of assets with all field values preserved.
**Validates: Requirements 6.1, 6.3**

### Property 10: Freed assets persistence round-trip
*For any* set of freed assets, saving them to the database and then loading them should result in an equivalent set of assets with all field values preserved.
**Validates: Requirements 6.2, 6.4**

### Property 11: Filter correctness
*For any* filter criteria (asset tag, user name, or team) and any set of assets, all returned results should match the filter criteria - containing the search term in the appropriate field.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 12: Filter clear restoration
*For any* filtered view of assets, clearing the filter should restore the display to show all assets in that category (active or freed).
**Validates: Requirements 7.5**

### Property 13: Initial load displays only active assets
*For any* database state containing both active and freed assets, starting the application should display only the non-freed assets on the Active Assets Page.
**Validates: Requirements 1.1**

## Error Handling

### Input Validation Errors
- **Duplicate Serial Number/Asset Tag**: Display clear error message indicating which field is duplicated
- **Missing Mandatory Fields**: Highlight missing fields and prevent submission
- **Invalid System Type**: Restrict input to "Laptop" or "Desktop" via dropdown

### Database Errors
- **Connection Failure**: Display error dialog and attempt to reconnect
- **Write Failure**: Show error message and retain data in memory for retry
- **Corruption**: Log error details and attempt recovery or suggest backup restoration

### UI Errors
- **Invalid Filter Input**: Ignore invalid characters and sanitize input
- **No Results Found**: Display friendly message indicating no matches

### Operation Errors
- **Delete Confirmation Cancelled**: Abort operation and maintain current state
- **Free Operation on Already Freed Asset**: Prevent operation and show warning
- **Delete Operation on Non-existent Asset**: Show error and refresh view

## Testing Strategy

### Unit Testing Framework
The application will use **pytest** as the testing framework for Python. Unit tests will cover:

- **Asset Manager Logic**: Test add, free, delete operations with specific examples
- **Validation Functions**: Test mandatory field validation, uniqueness checks
- **Database Operations**: Test CRUD operations with mock database
- **Filter Logic**: Test filter functions with specific search criteria
- **Edge Cases**: Empty inputs, special characters, boundary values

### Property-Based Testing Framework
The application will use **Hypothesis** for property-based testing in Python. Property-based tests will:

- Run a minimum of 100 iterations per property to ensure thorough coverage
- Generate random assets with varying field values
- Test universal properties across all possible inputs
- Each property-based test must include a comment tag in this format: `# Feature: asset-tracker, Property X: [property description]`
- Each correctness property from this design document must be implemented as a single property-based test
- Property tests should be placed close to implementation to catch errors early

### Integration Testing
- Test complete workflows: add → display → free → verify on Free Systems Page
- Test persistence: add assets → close app → reopen → verify data loaded
- Test filter workflows: apply filter → verify results → clear filter → verify all shown

### Test Data Strategy
- **Unit Tests**: Use specific, hand-crafted examples including edge cases
- **Property Tests**: Use Hypothesis strategies to generate random valid assets
- **Generators**: Create smart generators that produce valid serial numbers, asset tags, IP addresses, and team names

### Testing Approach
- Follow implementation-first development: implement features before writing tests
- Write both unit tests and property-based tests for comprehensive coverage
- Unit tests verify specific examples work correctly
- Property tests verify general correctness across many inputs
- Both types of tests are valuable and complement each other

## Implementation Notes

### Technology Stack
- **Language**: Python 3.8+
- **GUI Framework**: Tkinter (included with Python)
- **Database**: SQLite3 (included with Python)
- **Testing**: pytest, Hypothesis
- **Date/Time**: datetime module

### User Interface Design
- **Main Window**: Menu bar with "Active Assets" and "Free Systems" navigation
- **Asset Table**: Scrollable table with columns for all asset fields
- **Action Buttons**: Add, Free, Delete buttons with icons
- **Filter Panel**: Search fields for asset tag, user name, and team
- **Dialogs**: Modal dialogs for add asset form and delete confirmation

### Database Design Considerations
- Use SQLite for simplicity and portability (single file database)
- Create indexes on serial_number and asset_tag for fast lookups
- Use transactions for data integrity during operations
- Implement proper connection handling and cleanup

### Validation Rules
- **Serial Number**: Non-empty string, unique across all assets
- **Asset Tag (BIDC)**: Non-empty string, unique across all assets
- **System Type**: Must be exactly "Laptop" or "Desktop"
- **IP Address**: Optional, basic format validation (IPv4 pattern)
- **User Name**: Optional string
- **Team**: Optional string

### Future Enhancements (Out of Scope)
- Export to Excel/CSV functionality
- Asset history tracking (assignment changes over time)
- Multi-user access with authentication
- Network scanning for automatic IP detection
- Asset depreciation tracking
- Barcode/QR code scanning for asset tags
