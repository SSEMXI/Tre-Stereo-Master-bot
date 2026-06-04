"""
Configuration file for TRE BOT Discord Audio Services Bot
"""

# Audio Service Packages
PACKAGES = {
    "stereo_mastering": {
        "name": "Stereo Mastering",
        "price": 25,
        "currency": "$",
        "unit": "per song",
        "details": [
            "Loudness optimization",
            "EQ enhancement",
            "Compression",
            "Limiting",
            "Streaming-ready WAV & MP3"
        ],
        "description": "Professional stereo mastering to get your track radio-ready and optimized for all streaming platforms."
    },
    "recording_session": {
        "name": "Recording Session",
        "price": 40,
        "currency": "$",
        "unit": "per hour",
        "details": [
            "Professional microphone",
            "Vocal coaching/direction",
            "Multiple takes",
            "Session file export"
        ],
        "description": "Full recording session with professional equipment and expert guidance to capture your best vocal performance."
    },
    "full_song_package": {
        "name": "Full Song Package",
        "price": 150,
        "currency": "$",
        "unit": "per song",
        "details": [
            "Professional recording",
            "Expert mixing",
            "Professional mastering"
        ],
        "description": "Complete end-to-end production from recording through mixing to final mastered track."
    }
}

# Discord Bot Settings
COMMAND_PREFIX = "!"
