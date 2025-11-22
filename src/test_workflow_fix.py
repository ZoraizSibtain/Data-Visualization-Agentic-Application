"""
Test script to verify the workflow manager fix
"""
import os
os.environ['OPENAI_API_KEY'] = 'test-key-will-fail-but-tests-code-path'

from agents.python_repl_tool import SafePythonREPL
import config

# Test the REPL with figure generation
repl = SafePythonREPL(str(config.DATABASE_URL))

test_code = """
import pandas as pd
import plotly.express as px

# Create sample data
df = pd.DataFrame({
    'Product': ['A', 'B', 'C'],
    'Sales': [100, 200, 150]
})

# Create figure
fig = px.bar(df, x='Product', y='Sales')
result_json = fig.to_json()
"""

# Add the extraction code
modified_code = test_code + "\n\n# Print result for extraction\nif 'result_json' in dir():\n    print('<<<FIGURE_JSON_START>>>')\n    print(result_json)\n    print('<<<FIGURE_JSON_END>>>')"

print("Testing REPL with figure generation...")
result = repl.run(modified_code)

print("\n=== RESULT ===")
print(result[:500] if len(result) > 500 else result)

# Check if markers are present
if '<<<FIGURE_JSON_START>>>' in result:
    print("\n✅ Markers found in output!")
    start_marker = '<<<FIGURE_JSON_START>>>'
    end_marker = '<<<FIGURE_JSON_END>>>'
    start_idx = result.find(start_marker) + len(start_marker)
    end_idx = result.find(end_marker)
    
    if start_idx > 0 and end_idx > start_idx:
        json_str = result[start_idx:end_idx].strip()
        print(f"✅ Extracted JSON length: {len(json_str)} characters")
        
        # Validate JSON
        import json
        try:
            json.loads(json_str)
            print("✅ Valid JSON!")
        except Exception as e:
            print(f"❌ Invalid JSON: {e}")
else:
    print("\n❌ Markers NOT found in output")
