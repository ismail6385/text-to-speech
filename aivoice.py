import streamlit as st
import os
from gtts import gTTS
from pydub import AudioSegment
from pydub.effects import speedup, normalize
import time
from pathlib import Path
import tempfile
import base64

class ProfessionalTTS:
    def __init__(self, output_dir="audio_output"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
    def enhance_audio(self, audio_segment):
        """Enhance audio quality"""
        # Normalize audio
        audio = normalize(audio_segment)
        
        # Adjust bass and treble for clarity
        bass_multiplier = 3
        treble_multiplier = 1.5
        
        # Enhance bass (below 300Hz)
        temp = audio.low_pass_filter(300)
        bass = temp * bass_multiplier
        
        # Enhance treble (above 2000Hz)
        temp = audio.high_pass_filter(2000)
        treble = temp * treble_multiplier
        
        # Combine enhanced audio
        enhanced = audio.overlay(bass).overlay(treble)
        
        return enhanced
    
    def add_background_music(self, voice_audio, music_path, music_volume=-20):
        """Add background music to voice"""
        background = AudioSegment.from_file(music_path)
        
        if len(background) < len(voice_audio):
            times_to_loop = int(len(voice_audio) / len(background)) + 1
            background = background * times_to_loop
            
        background = background[:len(voice_audio)]
        background = background + music_volume
        
        return voice_audio.overlay(background)
    
    def create_audio(self, text, title, background_music=None, speed=1.0):
        """Create professional audio with enhanced quality"""
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/{title}_{timestamp}.mp3"
        
        tts = gTTS(text=text, lang='en', slow=False)
        temp_file = "temp.mp3"
        tts.save(temp_file)
        
        audio = AudioSegment.from_mp3(temp_file)
        audio = self.enhance_audio(audio)
        
        if speed != 1.0:
            audio = speedup(audio, playback_speed=speed)
        
        if background_music:
            audio = self.add_background_music(audio, background_music)
        
        audio.export(output_file, format="mp3", bitrate="192k")
        os.remove(temp_file)
        
        return output_file
    
    def batch_process(self, stories_dict, background_music=None, speed=1.0):
        """Process multiple stories at once"""
        results = {}
        for title, text in stories_dict.items():
            output_file = self.create_audio(text, title, background_music, speed)
            results[title] = output_file
        return results

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def main():
    st.set_page_config(
        page_title="Professional Text-to-Speech Generator",
        page_icon="🎙️",
        layout="wide"
    )

    st.title("🎙️ Professional Text-to-Speech Generator")
    st.markdown("Create high-quality audio content for your YouTube channel")

    st.sidebar.header("Settings")
    
    speed = st.sidebar.slider(
        "Speech Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1
    )

    tabs = st.tabs(["Single Story", "Batch Processing"])
    
    with tabs[0]:
        st.header("Single Story Generator")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            story_title = st.text_input("Story Title", "My Story")
            story_text = st.text_area(
                "Enter your story text",
                height=300,
                placeholder="Once upon a time..."
            )

        with col2:
            st.subheader("Audio Settings")
            
            background_music_file = st.file_uploader(
                "Upload Background Music (optional)",
                type=['mp3', 'wav']
            )
            
            music_volume = st.slider(
                "Background Music Volume",
                min_value=-30,
                max_value=0,
                value=-20
            )

        if st.button("Generate Audio", type="primary"):
            if story_text:
                with st.spinner("Generating audio..."):
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            tts_engine = ProfessionalTTS(temp_dir)
                            
                            bg_music_path = None
                            if background_music_file:
                                bg_music_path = os.path.join(temp_dir, "background.mp3")
                                with open(bg_music_path, "wb") as f:
                                    f.write(background_music_file.read())
                            
                            output_file = tts_engine.create_audio(
                                text=story_text,
                                title=story_title,
                                background_music=bg_music_path,
                                speed=speed
                            )
                            
                            audio_file = open(output_file, 'rb')
                            audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format='audio/mp3')
                            
                            st.markdown(
                                get_binary_file_downloader_html(output_file, 'audio file'),
                                unsafe_allow_html=True
                            )
                            
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter some text to generate audio.")

    with tabs[1]:
        st.header("Batch Story Processing")
        
        uploaded_files = st.file_uploader(
            "Upload text files (.txt)",
            type=['txt'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            stories = {}
            for file in uploaded_files:
                content = file.read().decode()
                stories[file.name] = content
            
            if st.button("Process All Stories", type="primary"):
                with st.spinner("Processing stories..."):
                    try:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            tts_engine = ProfessionalTTS(temp_dir)
                            results = tts_engine.batch_process(
                                stories,
                                background_music=None,
                                speed=speed
                            )
                            
                            st.success("All stories processed successfully!")
                            
                            for title, audio_file in results.items():
                                st.subheader(title)
                                audio_file = open(audio_file, 'rb')
                                audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format='audio/mp3')
                                st.markdown(
                                    get_binary_file_downloader_html(audio_file.name, f'audio for {title}'),
                                    unsafe_allow_html=True
                                )
                                
                    except Exception as e:
                        st.error(f"An error occurred during batch processing: {str(e)}")

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
        <p>Created for professional YouTube content creation</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
