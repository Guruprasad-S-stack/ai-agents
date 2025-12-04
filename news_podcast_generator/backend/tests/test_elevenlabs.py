"""
Test script for ElevenLabs Text-to-Speech
Run from backend folder: python tests/test_elevenlabs.py
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.env_loader import load_backend_env
load_backend_env()

def test_elevenlabs_basic():
    """Test basic ElevenLabs TTS with minimal text"""
    from elevenlabs.client import ElevenLabs
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        return False
    
    print(f"✓ API key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Initialize client
    try:
        client = ElevenLabs(api_key=api_key)
        print("✓ ElevenLabs client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test text
    test_text = "Hello, this is a test of the ElevenLabs text to speech system."
    voice_name = "Rachel"  # Default female voice
    
    print(f"\n📝 Test text: '{test_text}'")
    print(f"🎤 Voice: {voice_name}")
    print(f"🔄 Generating audio...")
    
    try:
        # Generate audio
        audio_generator = client.generate(
            text=test_text,
            voice=voice_name,
            model="eleven_multilingual_v2",
            stream=True,
        )
        
        # Collect audio chunks
        audio_chunks = []
        for chunk in audio_generator:
            if chunk:
                audio_chunks.append(chunk)
        
        if not audio_chunks:
            print("❌ No audio chunks received")
            return False
        
        audio_data = b"".join(audio_chunks)
        print(f"✓ Received {len(audio_data)} bytes of audio data")
        
        # Save to file
        output_path = os.path.join(os.path.dirname(__file__), "test_output.mp3")
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        file_size = os.path.getsize(output_path)
        print(f"✓ Audio saved to: {output_path}")
        print(f"✓ File size: {file_size / 1024:.2f} KB")
        
        print("\n✅ SUCCESS! ElevenLabs TTS is working correctly.")
        print(f"   You can play the test audio at: {output_path}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error generating audio: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_elevenlabs_voices():
    """Test if we can list voices (requires voices_read permission)"""
    from elevenlabs.client import ElevenLabs
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return
    
    print("\n" + "="*50)
    print("Testing voices.get_all() (requires voices_read permission)")
    print("="*50)
    
    try:
        client = ElevenLabs(api_key=api_key)
        voices = client.voices.get_all()
        print(f"✓ Found {len(voices.voices)} available voices:")
        for v in voices.voices[:5]:  # Show first 5
            print(f"   - {v.name} ({v.voice_id})")
        if len(voices.voices) > 5:
            print(f"   ... and {len(voices.voices) - 5} more")
    except Exception as e:
        print(f"⚠️  Cannot list voices: {e}")
        print("   This is OK if your API key lacks 'voices_read' permission.")
        print("   TTS generation can still work with voice names like 'Rachel', 'Adam'.")


if __name__ == "__main__":
    print("="*50)
    print("ElevenLabs TTS Test Script")
    print("="*50 + "\n")
    
    # Test basic TTS (the important one)
    success = test_elevenlabs_basic()
    
    # Test voice listing (optional, may fail with limited permissions)
    if success:
        test_elevenlabs_voices()
    
    print("\n" + "="*50)
    if success:
        print("All tests passed! ✅")
    else:
        print("Tests failed! ❌")
        print("\nTroubleshooting:")
        print("1. Check your ELEVENLABS_API_KEY in .env")
        print("2. Verify your ElevenLabs account has API access")
        print("3. Check if you have remaining character quota")
    print("="*50)

