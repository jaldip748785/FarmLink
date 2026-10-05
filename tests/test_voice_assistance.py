from utils.voice import sanitize_voice_text, get_voice_language


def test_sanitize_voice_text_strips_html_and_trims():
    assert sanitize_voice_text("<strong>Welcome</strong> to FarmLink!") == "Welcome to FarmLink!"


def test_get_voice_language_maps_supported_codes():
    assert get_voice_language("gu") == "gu-IN"
    assert get_voice_language("hi") == "hi-IN"
    assert get_voice_language("en") == "en-IN"
