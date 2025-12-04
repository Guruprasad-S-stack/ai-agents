"""
Test script to verify pydub can load MP3 files with FFmpeg.
Simulates the Celery worker environment where FFmpeg might not be in PATH.
"""
import os
import shutil
import tempfile

def test_pydub_ffmpeg():
    # SIMULATE CELERY: Remove FFmpeg from PATH
    print("=== SIMULATING CELERY (FFmpeg NOT in PATH) ===")
    original_path = os.environ.get("PATH", "")
    paths = [p for p in original_path.split(";") if "ffmpeg" not in p.lower()]
    os.environ["PATH"] = ";".join(paths)
    
    result = shutil.which("ffmpeg")
    print(f"shutil.which after removing from PATH: {result}")
    
    # Step 1: Find FFmpeg via WinGet search
    print("\n=== Finding FFmpeg via WinGet search ===")
    ffmpeg_path = None
    winget_packages = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
    if os.path.exists(winget_packages):
        for folder in os.listdir(winget_packages):
            if "FFmpeg" in folder:
                for root, dirs, files in os.walk(os.path.join(winget_packages, folder)):
                    if "ffmpeg.exe" in files:
                        ffmpeg_path = os.path.join(root, "ffmpeg.exe")
                        break
                if ffmpeg_path:
                    break
    
    print(f"Found via WinGet: {ffmpeg_path}")
    print(f"Exists: {os.path.exists(ffmpeg_path) if ffmpeg_path else False}")
    
    if not ffmpeg_path:
        print("ERROR: FFmpeg not found!")
        return False
    
    # Step 2: Add to PATH (THE FIX)
    print("\n=== Adding FFmpeg to PATH ===")
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    os.environ["PATH"] = ffmpeg_dir + ";" + os.environ.get("PATH", "")
    print(f"Added: {ffmpeg_dir}")
    result2 = shutil.which("ffmpeg")
    print(f"shutil.which now: {result2}")
    
    # Step 3: Configure pydub
    print("\n=== Configuring pydub ===")
    from pydub import AudioSegment
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffprobe = ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")
    print(f"AudioSegment.converter = {AudioSegment.converter}")
    print(f"AudioSegment.ffprobe = {AudioSegment.ffprobe}")
    
    # Step 4: Create test MP3
    print("\n=== Creating test MP3 with Edge TTS ===")
    import asyncio
    import edge_tts
    
    temp_dir = tempfile.mkdtemp(prefix="pydub_test_")
    test_file = os.path.join(temp_dir, "test.mp3")
    
    async def create_test_mp3():
        c = edge_tts.Communicate("Hello, this is a pydub FFmpeg test.", "en-US-GuyNeural")
        with open(test_file, "wb") as f:
            async for chunk in c.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
    
    asyncio.run(create_test_mp3())
    print(f"Created: {test_file}")
    print(f"Size: {os.path.getsize(test_file)} bytes")
    
    # Step 5: CRITICAL TEST - Load with pydub
    print("\n=== LOADING WITH PYDUB (CRITICAL TEST) ===")
    try:
        segment = AudioSegment.from_mp3(test_file)
        print(f"✅ SUCCESS! Loaded {len(segment)}ms of audio")
        success = True
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        success = False
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    # Restore PATH
    os.environ["PATH"] = original_path
    
    return success

if __name__ == "__main__":
    success = test_pydub_ffmpeg()
    print("\n" + "=" * 50)
    print(f"TEST RESULT: {'PASS' if success else 'FAIL'}")
    print("=" * 50)

