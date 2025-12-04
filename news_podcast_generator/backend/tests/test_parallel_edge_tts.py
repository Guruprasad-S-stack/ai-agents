"""
Test parallel Edge TTS generation - closer to actual audio_generate_agent code.
"""
import os
import shutil
import tempfile
import asyncio
import time

def setup_ffmpeg():
    """Find and configure FFmpeg."""
    ffmpeg_path = shutil.which("ffmpeg")
    
    if not ffmpeg_path:
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
    
    if ffmpeg_path:
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        os.environ["PATH"] = ffmpeg_dir + ";" + os.environ.get("PATH", "")
    
    return ffmpeg_path


async def test_parallel_generation():
    """Simulate the exact pattern used in audio_generate_agent."""
    import edge_tts
    from pydub import AudioSegment
    
    # Setup FFmpeg
    ffmpeg_path = setup_ffmpeg()
    if not ffmpeg_path:
        print("ERROR: FFmpeg not found!")
        return False
    
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffprobe = ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")
    print(f"FFmpeg: {ffmpeg_path}")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="edge_tts_test_")
    print(f"Temp dir: {temp_dir}")
    
    # Test data (5 segments)
    test_entries = [
        {"speaker": 1, "text": "Hello, welcome to our podcast."},
        {"speaker": 2, "text": "Thanks for having me, it's great to be here."},
        {"speaker": 1, "text": "Today we're discussing an important topic."},
        {"speaker": 2, "text": "Yes, this is really fascinating stuff."},
        {"speaker": 1, "text": "Thank you for listening!"},
    ]
    
    voice_map = {1: "en-US-GuyNeural", 2: "en-US-JennyNeural"}
    
    async def generate_segment(entry, index):
        """Generate a single TTS segment - same as audio_generate_agent."""
        text = entry.get("text", "").strip()
        speaker_id = entry.get("speaker", 1)
        
        if not text:
            return None
        
        voice = voice_map.get(speaker_id, "en-US-GuyNeural")
        temp_file = os.path.join(temp_dir, f"segment_{index:04d}.mp3")
        
        try:
            communicate = edge_tts.Communicate(text, voice)
            
            # Use stream() instead of save()
            with open(temp_file, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
            
            # Verify file was created
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                print(f"  ✓ Segment {index}: {os.path.getsize(temp_file)} bytes")
                return temp_file
            else:
                print(f"  ✗ Segment {index}: File empty or not created")
                return None
        except Exception as e:
            print(f"  ✗ Segment {index} failed: {e}")
            return None
    
    # Generate all segments in PARALLEL
    print("\n=== Generating segments in PARALLEL ===")
    start = time.time()
    tasks = [generate_segment(entry, i) for i, entry in enumerate(test_entries)]
    temp_files = await asyncio.gather(*tasks)
    gen_time = time.time() - start
    
    success_count = sum(1 for f in temp_files if f)
    print(f"\nGeneration complete: {success_count}/{len(test_entries)} in {gen_time:.1f}s")
    
    # Debug: List actual files
    print(f"\n=== Files in temp dir ===")
    actual_files = os.listdir(temp_dir)
    print(f"os.listdir: {actual_files}")
    
    # Debug: Check temp_files list
    print(f"\n=== temp_files list ===")
    for i, f in enumerate(temp_files):
        print(f"  [{i}] {f}")
        if f:
            print(f"       exists={os.path.exists(f)}, size={os.path.getsize(f) if os.path.exists(f) else 'N/A'}")
    
    # CRITICAL: Try to combine with pydub
    print(f"\n=== Combining with pydub ===")
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=500)
    
    for i, temp_file in enumerate(temp_files):
        if temp_file and os.path.exists(temp_file):
            try:
                segment = AudioSegment.from_mp3(temp_file)
                if len(combined) > 0:
                    combined += silence
                combined += segment
                print(f"  ✓ Loaded segment {i}: {len(segment)}ms")
            except Exception as e:
                print(f"  ✗ Could not load segment {i}: {e}")
    
    if len(combined) == 0:
        print("❌ No audio segments could be combined")
        shutil.rmtree(temp_dir)
        return False
    
    # Export
    output_path = os.path.join(os.path.dirname(__file__), "test_parallel_output.mp3")
    combined.export(output_path, format="mp3")
    print(f"\n✅ SUCCESS! Saved {len(combined)/1000:.1f}s to {output_path}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_parallel_generation())
    print("\n" + "=" * 50)
    print(f"TEST RESULT: {'PASS' if success else 'FAIL'}")
    print("=" * 50)

