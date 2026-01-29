# TUI Scroll Enhancement

## Overview
Added comprehensive scroll support to all TUI panels to handle small terminal heights.

## Changes

### CSS Modifications (`app/ui/app.py`)

#### 1. Menu Panel Scroll
```css
#menu_panel {
    overflow-y: auto;
    scrollbar-gutter: stable;
}
```
- Enables vertical scrolling for menu buttons
- Useful when terminal height is limited

#### 2. Content Panel Scroll
```css
#content_panel {
    overflow-y: auto;
    scrollbar-gutter: stable;
}
```
- Main content area now scrollable
- Projects, scenarios, results lists can scroll

#### 3. Content Area Auto Height
```css
#content_area {
    width: 100%;
    height: auto;
}
```
- Static widget expands to full content height
- Works with parent container scroll

#### 4. Analysis Content Scroll
```css
#analysis_content {
    overflow-y: auto;
    scrollbar-gutter: stable;
}
```
- Result analysis data scrollable
- Handles long metric lists

#### 5. UML Section Scroll
```css
#uml_section {
    overflow-y: auto;
    scrollbar-gutter: stable;
}
```
- API flow diagrams scrollable
- PlantUML/ASCII diagrams can be long

#### 6. Log Section Scroll
```css
#log_section {
    overflow-y: auto;
    scrollbar-gutter: stable;
}
```
- Detailed logs scrollable
- Step-by-step execution logs

## Benefits

### 1. Small Terminal Support
- Works on terminals with limited height (e.g., 24 lines)
- All content accessible via scroll

### 2. Stable Layout
- `scrollbar-gutter: stable` prevents layout shift
- Scrollbar space always reserved

### 3. Better UX
- No content hidden or cut off
- Mouse wheel and keyboard navigation work

### 4. Consistent Behavior
- All panels have uniform scroll behavior
- Predictable user experience

## Usage

### Keyboard Navigation
- **↑/↓**: Scroll up/down
- **Page Up/Down**: Jump scroll
- **Home/End**: Jump to start/end

### Mouse Navigation
- **Scroll wheel**: Natural scrolling
- **Scrollbar drag**: Direct position control

## Testing

### Test on Small Terminal
```bash
# Set terminal to minimal height
resize -s 24 80

# Run simulator
./run.sh

# Navigate to different screens
# - Projects (p)
# - Scenarios (s)
# - Results (r)
# - UML (u)
```

### Expected Behavior
- All content visible via scroll
- No layout glitches
- Smooth scrolling experience
- Scrollbar appears when needed

## Technical Details

### Scrollable Panels
1. **Menu Panel**: Button list (left sidebar)
2. **Content Panel**: Main content area (right side)
3. **Content Area**: Static widget inside content panel
4. **Analysis Content**: Result data panel (split view left)
5. **UML Section**: Diagram panel (split view right top)
6. **Log Section**: Log panel (split view right bottom)

### Non-Scrollable Elements
1. **Header**: Always visible (app title, clock)
2. **Footer**: Always visible (key bindings)
3. **Status Bar**: Always visible (status messages)
4. **Input Container**: Always visible (command input)

## Backward Compatibility
- No breaking changes
- Existing functionality unchanged
- Pure CSS enhancement

## Related Issues
- Terminal height limitation
- Content visibility issues
- UX improvement for compact displays
