# File: `app/modules/admin/notices.py`

## Overview
A simpler version of notice management (possibly legacy or redundant). The comprehensive version typically resides in `notices_mgmt.py`.

## Routes

### `/notices` (GET)
*   **Purpose**: List all notices.
*   **Returns**: `notice_list.html`.

### `/notices/add` (GET, POST)
*   **Purpose**: Add a basic notice (Title/Content/Audience string).
*   **Logic**: Creates `Notice` object.
*   **Returns**: Redirects to list.
