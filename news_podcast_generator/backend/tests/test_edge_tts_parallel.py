"""
Test Edge TTS with PARALLEL processing for faster generation.
Loads the real script and generates audio using concurrent API calls.

Run from backend folder: python tests/test_edge_tts_parallel.py
"""
import os
import sys
import asyncio
import json
import sqlite3
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.env_loader import load_backend_env
load_backend_env()


# ============================================================
# Edge TTS Voice Configuration
# ============================================================

VOICE_MAP = {
    "ALEX": "en-US-GuyNeural",
    "MORGAN": "en-US-AriaNeural",
}


# ============================================================
# Load Script from Database
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
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, state, created_at 
            FROM session_state 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        if row:
            state = json.loads(row[1]) if row[1] else {}
            script = state.get('generated_script', {})
            if script and script.get('sections'):
                return script
        return None
    finally:
        conn.close()


# ============================================================
# Parallel TTS Generation
# ============================================================

async def generate_single_segment(dialog: dict, index: int, temp_dir: str):
    """Generate audio for a single dialog segment"""
    import edge_tts
    
    speaker = dialog.get("speaker", "ALEX")
    text = dialog.get("text", "")
    voice = VOICE_MAP.get(speaker, "en-US-GuyNeural")
    
    temp_path = os.path.join(temp_dir, f"segment_{index:04d}.mp3")
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(temp_path)
    
    return index, temp_path


async def generate_audio_parallel(script_data: dict, output_path: str) -> bool:
    """Generate podcast audio using PARALLEL Edge TTS calls"""
    import edge_tts
    from pydub import AudioSegment
    import tempfile
    
    print("\n🎙️ Generating Audio with PARALLEL Edge TTS")
    print(f"   Voices: ALEX = {VOICE_MAP['ALEX']}, MORGAN = {VOICE_MAP['MORGAN']}")
    
    # Collect all dialogs
    all_dialogs = []
    for section in script_data.get("sections", []):
        for dialog in section.get("dialog", []):
            if dialog.get("text", "").strip():
                all_dialogs.append(dialog)
    
    print(f"\n🔄 Processing {len(all_dialogs)} dialog segments IN PARALLEL...")
    
    start_time = time.time()
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Generate ALL segments in parallel
        print("   ⚡ Sending all requests simultaneously...")
        
        tasks = [
            generate_single_segment(dialog, i, temp_dir)
            for i, dialog in enumerate(all_dialogs)
        ]
        
        # Run all tasks in parallel
        results = await asyncio.gather(*tasks)
        
        tts_time = time.time() - start_time
        print(f"   ✅ All TTS calls completed in {tts_time:.1f} seconds")
        
        # Sort results by index to maintain order
        results.sort(key=lambda x: x[0])
        
        # Combine audio files
        print("   🔗 Combining audio segments...")
        combine_start = time.time()
        
        combined = None
        for index, temp_path in results:
            segment = AudioSegment.from_mp3(temp_path)
            
            if combined is None:
                combined = segment
            else:
                pause = AudioSegment.silent(duration=300)
                combined = combined + pause + segment
        
        combine_time = time.time() - combine_start
        print(f"   ✅ Combined in {combine_time:.1f} seconds")
        
        # Export final audio
        print("   💾 Saving final audio...")
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        combined.export(output_path, format="mp3")
        
        total_time = time.time() - start_time
        file_size = os.path.getsize(output_path)
        duration = len(combined) / 1000
        
        print(f"\n{'='*60}")
        print("✅ SUCCESS! Audio generated!")
        print('='*60)
        print(f"   📁 File: {output_path}")
        print(f"   📦 Size: {file_size / 1024:.2f} KB ({file_size / 1024 / 1024:.2f} MB)")
        print(f"   🎵 Audio Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"\n⏱️ TIMING BREAKDOWN:")
        print(f"   TTS Generation (parallel): {tts_time:.1f} seconds")
        print(f"   Audio Combining: {combine_time:.1f} seconds")
        print(f"   ─────────────────────────────")
        print(f"   TOTAL TIME: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"\n🚀 Speed ratio: {duration/total_time:.2f}x real-time")
        print(f"📊 Compared to sequential (~102s): {102/total_time:.1f}x FASTER!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup temp files
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


# ============================================================
# Main
# ============================================================

async def main():
    print("="*60)
    print("Edge TTS PARALLEL Processing Test")
    print("="*60)
    
    # Load script
    print("\n📂 Loading script from database...")
    script_data = load_script_from_database()
    
    if not script_data:
        print("❌ No script found!")
        return
    
    # Count dialogs
    total_dialogs = sum(
        len(s.get("dialog", [])) 
        for s in script_data.get("sections", [])
    )
    total_chars = sum(
        len(d.get("text", ""))
        for s in script_data.get("sections", [])
        for d in s.get("dialog", [])
    )
    
    print(f"✅ Found script: {script_data.get('title', 'Unknown')}")
    print(f"   Dialogs: {total_dialogs}")
    print(f"   Characters: {total_chars}")
    
    # Generate audio
    output_path = os.path.join(os.path.dirname(__file__), "test_edge_tts_parallel_output.mp3")
    
    success = await generate_audio_parallel(script_data, output_path)
    
    if success:
        print(f"\n🎧 AUDIO READY! File saved to:")
        print(f"   {output_path}")
        print(f"\n💰 Cost: $0.00 (FREE!)")


if __name__ == "__main__":
    # Refresh PATH for FFmpeg
    os.environ["PATH"] = (
        os.environ.get("PATH", "") + ";" + 
        r"C:\ProgramData\chocolatey\bin" + ";" +
        r"C:\ffmpeg\bin"
    )
    
    asyncio.run(main())

