"""
Test Edge TTS with the ACTUAL podcast script generated from the workflow.
Loads the real script from the database and generates audio.

Run from backend folder: python tests/test_edge_tts_real_script.py
"""
import os
import sys
import asyncio
import json
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.env_loader import load_backend_env
load_backend_env()


# ============================================================
# Edge TTS Voice Configuration
# ============================================================

VOICE_MAP = {
    "ALEX": "en-US-GuyNeural",      # Male voice
    "MORGAN": "en-US-AriaNeural",   # Female voice
}


# ============================================================
# Load Real Script from Database
# ============================================================

def load_script_from_database():
    """Load the generated script from the session database"""
    
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "databases",
        "internal_sessions.db"
    )
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return None
    
    print(f"📂 Loading from: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the most recent session with a generated script
        cursor.execute("""
            SELECT session_id, state, created_at 
            FROM session_state 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ No sessions found in database")
            return None
        
        print(f"\n📋 Found {len(rows)} recent sessions:")
        
        for i, (session_id, state_json, updated_at) in enumerate(rows):
            try:
                state = json.loads(state_json) if state_json else {}
                script = state.get("generated_script", {})
                has_script = bool(script and script.get("sections"))
                
                print(f"   {i+1}. {session_id[:20]}... | Script: {'✅' if has_script else '❌'} | {updated_at}")
                
                if has_script:
                    return script
                    
            except json.JSONDecodeError:
                continue
        
        print("\n❌ No session with generated script found")
        return None
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None
    finally:
        conn.close()


def print_script_info(script_data: dict):
    """Print information about the loaded script"""
    print("\n" + "="*60)
    print("LOADED SCRIPT INFO")
    print("="*60)
    
    title = script_data.get("title", "Unknown")
    sections = script_data.get("sections", [])
    
    print(f"\n📝 Title: {title}")
    print(f"📑 Sections: {len(sections)}")
    
    total_dialogs = 0
    total_chars = 0
    
    for section in sections:
        section_type = section.get("type", "unknown")
        dialogs = section.get("dialog", [])
        chars = sum(len(d.get("text", "")) for d in dialogs)
        total_dialogs += len(dialogs)
        total_chars += chars
        print(f"   - {section_type}: {len(dialogs)} dialogs, {chars} chars")
    
    print(f"\n📊 Total: {total_dialogs} dialogs, {total_chars} characters")
    
    # Show first few dialogs
    print("\n🎤 First 5 dialog turns:")
    print("-"*40)
    count = 0
    for section in sections:
        for dialog in section.get("dialog", []):
            if count >= 5:
                break
            speaker = dialog.get("speaker", "?")
            text = dialog.get("text", "")[:60]
            print(f"   [{speaker}]: \"{text}{'...' if len(dialog.get('text', '')) > 60 else ''}\"")
            count += 1
        if count >= 5:
            break
    
    if total_dialogs > 5:
        print(f"   ... and {total_dialogs - 5} more dialogs")
    
    return total_dialogs, total_chars


# ============================================================
# Generate Audio with Edge TTS
# ============================================================

async def generate_audio_edge_tts(script_data: dict, output_path: str) -> bool:
    """Generate podcast audio using Edge TTS"""
    import time
    try:
        import edge_tts
        from pydub import AudioSegment
        import tempfile
    except ImportError as e:
        print(f"\n❌ Missing package: {e}")
        return False
    
    print("\n🎙️ Generating Audio with Edge TTS")
    print(f"   Voices: ALEX = {VOICE_MAP['ALEX']}, MORGAN = {VOICE_MAP['MORGAN']}")
    
    start_time = time.time()
    
    # Collect all dialogs
    all_dialogs = []
    for section in script_data.get("sections", []):
        for dialog in section.get("dialog", []):
            if dialog.get("text", "").strip():
                all_dialogs.append(dialog)
    
    print(f"\n🔄 Processing {len(all_dialogs)} dialog segments...")
    
    temp_files = []
    combined = None
    
    try:
        for i, dialog in enumerate(all_dialogs):
            speaker = dialog.get("speaker", "ALEX")
            text = dialog.get("text", "")
            voice = VOICE_MAP.get(speaker, "en-US-GuyNeural")
            
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            temp_files.append(temp_path)
            
            # Generate audio
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)
            
            # Load and combine
            segment = AudioSegment.from_mp3(temp_path)
            
            if combined is None:
                combined = segment
            else:
                pause = AudioSegment.silent(duration=300)
                combined = combined + pause + segment
            
            # Progress
            if (i + 1) % 10 == 0 or i == len(all_dialogs) - 1:
                print(f"   Processed {i + 1}/{len(all_dialogs)} segments...")
        
        # Export
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        combined.export(output_path, format="mp3")
        
        file_size = os.path.getsize(output_path)
        duration = len(combined) / 1000
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n✅ SUCCESS! Audio generated!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size / 1024:.2f} KB ({file_size / 1024 / 1024:.2f} MB)")
        print(f"   Audio Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"\n⏱️ GENERATION TIME: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"   Speed ratio: {duration/total_time:.2f}x real-time")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass


# ============================================================
# Main
# ============================================================

async def main():
    print("="*60)
    print("Edge TTS Test with REAL Podcast Script")
    print("="*60)
    
    # Step 1: Load script from database
    print("\n📂 STEP 1: Loading script from database...")
    script_data = load_script_from_database()
    
    if not script_data:
        print("\n💡 No script found. Generate a podcast first using the app!")
        print("   Or the script format might be different.")
        return
    
    # Step 2: Show script info
    total_dialogs, total_chars = print_script_info(script_data)
    
    # Step 3: Estimate time
    print("\n⏱️ ESTIMATED TIME:")
    est_time = total_dialogs * 2  # ~2 seconds per segment
    print(f"   ~{est_time} seconds ({est_time/60:.1f} minutes) to generate")
    
    # Confirm
    print("\n" + "="*60)
    response = input("Proceed with audio generation? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    # Step 4: Generate audio
    output_path = os.path.join(os.path.dirname(__file__), "test_edge_tts_real_output.mp3")
    
    success = await generate_audio_edge_tts(script_data, output_path)
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ TEST PASSED!")
        print(f"\n🎧 Play the REAL podcast audio:")
        print(f"   {output_path}")
        print(f"\n💰 Cost: $0.00 (Edge TTS is FREE!)")
        print(f"\n📊 Comparison:")
        print(f"   - ElevenLabs would cost: ~${total_chars * 0.00022:.2f}")
        print(f"   - Edge TTS cost: $0.00")
    else:
        print("❌ TEST FAILED")
    print("="*60)


if __name__ == "__main__":
    # Refresh PATH for FFmpeg
    import os
    os.environ["PATH"] = os.environ.get("PATH", "") + ";" + r"C:\ProgramData\chocolatey\bin"
    
    asyncio.run(main())

