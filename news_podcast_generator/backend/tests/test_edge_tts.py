"""
Test script for Edge TTS with SSML Voice Switching
FREE, unlimited, works immediately!

Run from backend folder: python tests/test_edge_tts.py
"""
import os
import sys
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# STEP 1: Sample Podcast Script (mimics script_agent.py output)
# ============================================================

SAMPLE_PODCAST_SCRIPT = {
    "title": "Agentic AI: The Next Frontier - December 2024",
    "sections": [
        {
            "type": "intro",
            "title": None,
            "dialog": [
                {"speaker": "ALEX", "text": "Welcome back to Tech Insights! I'm Alex."},
                {"speaker": "MORGAN", "text": "And I'm Morgan. Today we're diving into agentic AI."},
                {"speaker": "ALEX", "text": "This is one of the hottest topics in tech right now."},
                {"speaker": "MORGAN", "text": "Absolutely! Let's break it down for our listeners."},
            ]
        },
        {
            "type": "article",
            "title": "What is Agentic AI?",
            "dialog": [
                {"speaker": "ALEX", "text": "So Morgan, what exactly is agentic AI?"},
                {"speaker": "MORGAN", "text": "Great question! It's AI that can take autonomous actions."},
                {"speaker": "ALEX", "text": "You mean like making decisions on its own?"},
                {"speaker": "MORGAN", "text": "Exactly. It can plan, execute, and adapt without constant human input."},
                {"speaker": "ALEX", "text": "That's a big shift from traditional chatbots."},
                {"speaker": "MORGAN", "text": "Huge shift. We're talking about AI that can actually get things done."},
            ]
        },
        {
            "type": "outro",
            "title": None,
            "dialog": [
                {"speaker": "ALEX", "text": "Well, that's all the time we have for today."},
                {"speaker": "MORGAN", "text": "Thanks for listening everyone!"},
                {"speaker": "ALEX", "text": "See you next time on Tech Insights."},
                {"speaker": "MORGAN", "text": "Bye for now!"},
            ]
        }
    ],
    "sources": ["https://example.com/agentic-ai"]
}


# ============================================================
# Edge TTS Voice Options
# ============================================================

# Recommended conversational voices
VOICE_MAP = {
    "ALEX": "en-US-GuyNeural",      # Male, friendly conversational
    "MORGAN": "en-US-AriaNeural",   # Female, friendly conversational
}

# Alternative voices you can try:
# Male: en-US-DavisNeural, en-US-TonyNeural, en-US-JasonNeural
# Female: en-US-JennyNeural, en-US-SaraNeural, en-US-NancyNeural


# ============================================================
# STEP 2: Convert Script to SSML with Voice Switching
# ============================================================

def convert_script_to_ssml(script_data: dict) -> str:
    """
    Convert podcast script to SSML with voice switching.
    Each speaker gets their own <voice> tag.
    """
    ssml_parts = ['<speak>']
    
    for section in script_data.get("sections", []):
        for dialog in section.get("dialog", []):
            speaker = dialog.get("speaker", "ALEX")
            text = dialog.get("text", "")
            voice = VOICE_MAP.get(speaker, "en-US-GuyNeural")
            
            if text.strip():
                # Escape special XML characters
                text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                # Add voice tag with text
                ssml_parts.append(f'    <voice name="{voice}">{text}</voice>')
                # Add small pause between speakers
                ssml_parts.append('    <break time="300ms"/>')
    
    ssml_parts.append('</speak>')
    return '\n'.join(ssml_parts)


def print_ssml_preview(ssml: str):
    """Print SSML preview"""
    print("\n" + "="*60)
    print("SSML PREVIEW (first 20 lines)")
    print("="*60)
    
    lines = ssml.split('\n')
    for line in lines[:20]:
        print(line)
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")


# ============================================================
# STEP 3: Generate Audio with Edge TTS
# ============================================================

async def generate_audio_edge_tts_ssml(ssml: str, output_path: str) -> bool:
    """
    Generate audio using Edge TTS with SSML voice switching.
    Note: Edge TTS processes SSML but may handle voice switching differently.
    """
    try:
        import edge_tts
    except ImportError:
        print("\n❌ edge-tts not installed!")
        print("Run: pip install edge-tts")
        return False
    
    try:
        print("\n🔄 Generating podcast audio with Edge TTS...")
        print("   Using SSML with voice switching...")
        
        # Edge TTS with SSML
        communicate = edge_tts.Communicate(ssml, voice="en-US-GuyNeural")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        await communicate.save(output_path)
        
        file_size = os.path.getsize(output_path)
        print(f"\n✅ Audio generated!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size / 1024:.2f} KB")
        return True
        
    except Exception as e:
        print(f"\n⚠️ SSML mode failed: {e}")
        print("   Trying alternative approach...")
        return False


async def generate_audio_edge_tts_segments(script_data: dict, output_path: str) -> bool:
    """
    Alternative: Generate audio by processing each dialog turn separately,
    then combining them. More reliable than SSML.
    """
    try:
        import edge_tts
        from pydub import AudioSegment
        import tempfile
    except ImportError as e:
        print(f"\n❌ Missing package: {e}")
        print("Run: pip install edge-tts pydub")
        return False
    
    print("\n🔄 Generating podcast audio (segment-by-segment)...")
    
    temp_files = []
    combined = None
    
    try:
        # Process each dialog turn
        all_dialogs = []
        for section in script_data.get("sections", []):
            for dialog in section.get("dialog", []):
                all_dialogs.append(dialog)
        
        print(f"   Processing {len(all_dialogs)} dialog segments...")
        
        for i, dialog in enumerate(all_dialogs):
            speaker = dialog.get("speaker", "ALEX")
            text = dialog.get("text", "")
            voice = VOICE_MAP.get(speaker, "en-US-GuyNeural")
            
            if not text.strip():
                continue
            
            # Create temp file for this segment
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            temp_files.append(temp_path)
            
            # Generate audio for this segment
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)
            
            # Load and combine
            segment = AudioSegment.from_mp3(temp_path)
            
            if combined is None:
                combined = segment
            else:
                # Add 300ms pause between speakers
                pause = AudioSegment.silent(duration=300)
                combined = combined + pause + segment
            
            # Progress indicator
            if (i + 1) % 5 == 0 or i == len(all_dialogs) - 1:
                print(f"   Processed {i + 1}/{len(all_dialogs)} segments...")
        
        # Export final audio
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        combined.export(output_path, format="mp3")
        
        file_size = os.path.getsize(output_path)
        duration = len(combined) / 1000  # milliseconds to seconds
        
        print(f"\n✅ SUCCESS! Podcast audio generated!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size / 1024:.2f} KB")
        print(f"   Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass


# ============================================================
# STEP 4: Main Test
# ============================================================

async def main():
    print("="*60)
    print("Edge TTS - Multi-Voice Podcast Test")
    print("FREE & UNLIMITED!")
    print("="*60)
    
    # Step 1: Show script info
    print("\n📝 STEP 1: Sample Podcast Script")
    print(f"   Title: {SAMPLE_PODCAST_SCRIPT['title']}")
    
    total_dialogs = sum(len(s.get("dialog", [])) for s in SAMPLE_PODCAST_SCRIPT["sections"])
    total_chars = sum(
        len(d.get("text", "")) 
        for s in SAMPLE_PODCAST_SCRIPT["sections"] 
        for d in s.get("dialog", [])
    )
    print(f"   Dialog turns: {total_dialogs}")
    print(f"   Total characters: {total_chars}")
    
    # Step 2: Show SSML conversion
    print("\n🔄 STEP 2: Converting to SSML...")
    ssml = convert_script_to_ssml(SAMPLE_PODCAST_SCRIPT)
    print_ssml_preview(ssml)
    
    # Step 3: Generate audio (using segment approach for reliability)
    print("\n🎙️ STEP 3: Generating Audio")
    print(f"   Voices: ALEX = {VOICE_MAP['ALEX']}, MORGAN = {VOICE_MAP['MORGAN']}")
    
    output_path = os.path.join(os.path.dirname(__file__), "test_edge_tts_output.mp3")
    
    # Use segment-by-segment approach (more reliable)
    success = await generate_audio_edge_tts_segments(SAMPLE_PODCAST_SCRIPT, output_path)
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ TEST PASSED!")
        print(f"\n🎧 Play the audio to hear the multi-voice podcast:")
        print(f"   {output_path}")
        print("\n💰 Cost: $0.00 (Edge TTS is FREE and UNLIMITED!)")
    else:
        print("❌ TEST FAILED")
        print("\nTroubleshooting:")
        print("1. pip install edge-tts pydub")
        print("2. Install ffmpeg for pydub audio processing")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

