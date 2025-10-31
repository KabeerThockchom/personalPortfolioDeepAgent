# Enhanced Terminal Display

## Summary

The chat interface now displays detailed tool inputs and outputs during execution, including special handling for subagent tool calls with visual indentation and context.

## What's New

### 1. **Full Input Arguments Display**

Previously, tool arguments were truncated to 100 characters. Now:
- **Full arguments** shown for most tools (up to 300 chars with smart truncation)
- **JSON formatting** for complex dict/list arguments
- **Specialized display** for different tool types:
  - File operations show file paths and content previews
  - Yahoo Finance tools show symbols and parameters
  - Web searches show queries and filters
  - Subagent spawns show full descriptions

**Example:**
```
📊 Yahoo Finance API: get_stock_quote
   Symbol(s): AAPL
   region: US
   lang: en-US
```

### 2. **Enhanced Result Display**

Previously, results were truncated to 200 characters. Now:
- **Smart parsing** - Detects JSON and dict structures
- **Success/Error indicators** - Visual status with color coding
- **Summaries** - Shows formatted summaries from API responses
- **Key metrics** - Extracts and displays important metrics
- **File paths** - Shows where data was saved
- **Multi-line support** - Properly formats long text

**Example:**
```
✓ Result:
  ✓ SUCCESS
  Symbol: AAPL
  📊 Stock Quote for AAPL

  Price: $150.25 (+2.50, +1.69%)
  Market Cap: $2.4T
  P/E Ratio: 28.5

  Key Metrics:
    • price: 150.25
    • change: 2.5
    • changePercent: 1.69

  Saved to: /financial_data/AAPL_quote.json
```

### 3. **Subagent Tool Call Detection**

The display now detects and highlights subagent execution:
- **Visual boxes** around subagent steps
- **Indentation** for all subagent tool calls and results
- **Subagent name** displayed in step header
- **Clear boundaries** with decorative box drawing

**Example:**
```
╭─── Subagent Step 5: market-data-fetcher ───╮

  📊 Yahoo Finance API: get_multiple_quotes
     Symbol(s): ['AAPL', 'MSFT', 'GOOGL']
     region: US

  [get_multiple_quotes] returned:
     ✓ Result:
       ✓ SUCCESS
       Fetched quotes for 3 symbols

       AAPL: $150.25 (+1.69%)
       MSFT: $330.15 (-0.36%)
       GOOGL: $140.50 (+0.82%)

╰──────────────────────────────────────────────╯
```

## Features in Detail

### Tool Call Display (`print_tool_call`)

**Special handling for:**

1. **Subagent spawning** (`task` tool)
   - Shows subagent type prominently
   - Displays full description with line wrapping
   - Color: Yellow/Warning

2. **File operations**
   - `write_file` - Shows path and content preview (150 chars)
   - `edit_file` - Shows path, old/new string previews
   - `read_file` - Shows file path
   - `ls` - Shows directory path
   - Color: Blue/Cyan

3. **Todo planning** (`write_todos`)
   - Shows number of tasks
   - Lists first 3 tasks
   - Color: Yellow/Warning

4. **Yahoo Finance tools** (`get_*` tools)
   - Shows tool name and symbol(s)
   - Displays all relevant parameters
   - Color: Green

5. **Web search tools**
   - Shows query and filters
   - Displays max_results if specified
   - Color: Green

6. **Generic tools**
   - Shows all arguments formatted as JSON
   - Handles multiline values
   - Color: Green

### Result Display (`print_tool_result`)

**Intelligent formatting based on type:**

1. **Dict results**
   - Detects `success` field → Shows ✓ SUCCESS / ✗ FAILED
   - Extracts `symbol` if present
   - Displays `summary` with line wrapping (first 10 lines)
   - Shows `key_metrics` (first 5)
   - Highlights `file_path` if data was saved
   - Shows `error` message if failed
   - Previews `data` if no summary available

2. **List results**
   - Shows total count
   - Displays first 3 items
   - Indicates remaining items

3. **String results**
   - Shows full text if < 500 chars
   - Truncates with "..." if longer
   - Preserves line breaks

### Smart Value Formatting (`format_value`)

Helper function for displaying complex values:
- **Dicts** → Pretty-printed JSON with indentation
- **Lists** → Shows first 5 items + count
- **Strings** → Truncates to max_length with indicator
- **Max length** → Configurable (default 500 chars for args, varies for results)

## Visual Hierarchy

The display uses indentation to show execution context:

```
Main Agent (no indent)
├─ Tool call
├─ Result
│
├─ Subagent spawn
│  ╭─── Subagent Step ───╮
│  │  Tool call (indented)
│  │  Result (indented)
│  │  Files updated (indented)
│  ╰─────────────────────╯
│
└─ Final response
```

## Color Coding

- **Yellow/Warning** - Important actions (subagent spawn, todos)
- **Blue** - File operations, results
- **Cyan** - File reads, directory listings, subagent boxes
- **Green** - Tool calls, success status
- **Red** - Errors, failures

## Benefits

1. **Better debugging** - See exactly what's being passed to tools
2. **Transparency** - Understand what subagents are doing
3. **Context awareness** - Visual hierarchy shows execution flow
4. **Data visibility** - See summaries and key metrics without reading files
5. **Error tracking** - Clear indication of failures with error messages

## Files Modified

- **chat.py** - Enhanced `print_tool_call()`, `print_tool_result()`, added `format_value()`
- **chat.py** - Added subagent detection in execution loop
- **chat.py** - Updated banner to mention new features

## Testing

Run the test script to see all display features:
```bash
python3 test_enhanced_display.py
```

This shows examples of:
- Simple tool calls
- Yahoo Finance API calls
- Subagent spawning
- Results with success/error
- List results
- Long text results
- Indented subagent displays

## Configuration

**Adjustable limits in code:**
- `format_value(value, max_length=500)` - Max chars for formatted values
- `print_tool_call` - Content preview: 150 chars, todo list: first 3
- `print_tool_result` - Summary lines: 10, key metrics: 5, list items: 3

## Examples from Real Usage

### Portfolio Analysis Flow

```
━━━ Step 1: model ━━━
📋 Planning 3 tasks
   1. Load portfolio from /financial_data/
   2. Fetch current prices for all holdings
   3. Calculate portfolio value and allocation

🚀 SPAWNING SUBAGENT: market-data-fetcher
   Description: Fetch current prices for AAPL, MSFT, GOOGL, NVDA to calculate
   Description: portfolio value

  ╭─── Subagent Step 3: market-data-fetcher ───╮

    📊 Yahoo Finance API: get_multiple_quotes
       Symbol(s): ['AAPL', 'MSFT', 'GOOGL', 'NVDA']
       region: US

    [get_multiple_quotes] returned:
       ✓ Result:
         ✓ SUCCESS
         📊 Fetched quotes for 4 symbols

         Key Metrics:
           • symbols_fetched: 4
           • total_market_cap: $8.9T

         Saved to: /financial_data/current_prices.json

  ╰──────────────────────────────────────────────╯

📝 Writing file: /financial_data/portfolio_analysis.json
   Content preview: {"total_value": 125000, "allocation": {"stocks": 0.70, "bonds": 0.30}...
```

### Error Handling Example

```
  ╭─── Subagent Step 8: market-data-fetcher ───╮

    📊 Yahoo Finance API: get_stock_quote
       Symbol(s): INVALID_TICKER
       region: US

    [get_stock_quote] returned:
       ✓ Result:
         ✗ FAILED
         Symbol: INVALID_TICKER
         Error: Symbol not found. Please check ticker symbol.

  ╰──────────────────────────────────────────────╯
```

## Future Enhancements

Possible improvements:
- Collapsible sections for very long outputs
- Color themes (e.g., dark mode, light mode)
- Export execution logs to file
- Performance timing for each tool call
- Network traffic indicators for API calls
- Progress bars for long-running operations

## Conclusion

The enhanced display provides full visibility into:
- ✅ What tools are being called
- ✅ What arguments are being passed
- ✅ What results are being returned
- ✅ Which agent (main or subagent) is executing
- ✅ Success/failure status
- ✅ Where data is being saved

This makes the system much more transparent and easier to debug, while maintaining readability with smart truncation and formatting.
