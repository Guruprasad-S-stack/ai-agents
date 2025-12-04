"""Show the generated podcast script from the database"""
import sqlite3
import json
import os

# Check both possible database locations
db_paths = [
    "databases/internal_sessions.db",
    "databases/agent_sessions.db",
]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"\n{'='*60}")
        print(f"DATABASE: {db_path}")
        print('='*60)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        # Try to find the script
        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 1")
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                
                if row:
                    print(f"\n--- Table: {table} ---")
                    print(f"Columns: {columns}")
                    
                    # Look for state/data column with JSON
                    for i, col in enumerate(columns):
                        if col in ['state', 'data', 'session_state', 'value']:
                            try:
                                data = json.loads(row[i]) if row[i] else {}
                                script = data.get('generated_script', {})
                                if script and script.get('sections'):
                                    print(f"\n{'='*60}")
                                    print("FOUND PODCAST SCRIPT!")
                                    print('='*60)
                                    print(f"\nTitle: {script.get('title', 'Unknown')}")
                                    print(f"Sections: {len(script.get('sections', []))}")
                                    
                                    for section in script.get('sections', []):
                                        print(f"\n--- {section.get('type', 'unknown').upper()} ---")
                                        for dialog in section.get('dialog', []):
                                            speaker = dialog.get('speaker', '?')
                                            text = dialog.get('text', '')
                                            # Truncate long text
                                            if len(text) > 150:
                                                text = text[:150] + "..."
                                            print(f"[{speaker}]: {text}")
                                    
                                    conn.close()
                                    exit(0)
                            except:
                                pass
            except Exception as e:
                print(f"Error reading {table}: {e}")
        
        conn.close()

print("\nNo podcast script found in any database.")

