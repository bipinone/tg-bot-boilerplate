import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class I18nService:
    """Multi-language localization service with JSON locale files."""

    SUPPORTED_LANGUAGES: Dict[str, str] = {
        "en": "English 🇬🇧",
        "hi": "हिन्दी 🇮🇳"
    }

    def __init__(self, locales_dir: Optional[Path] = None):
        self.locales_dir = locales_dir or Path(__file__).parent / "locales"
        self._translations: Dict[str, Dict[str, str]] = {}
        self.load_locales()

    def load_locales(self) -> None:
        """Loads all JSON translation files from locales directory."""
        if not self.locales_dir.exists():
            logger.warning("Locales directory not found at: %s", self.locales_dir)
            return

        for file_path in self.locales_dir.glob("*.json"):
            lang = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._translations[lang] = json.load(f)
                logger.debug("Loaded locale '%s' (%d keys)", lang, len(self._translations[lang]))
            except Exception as e:
                logger.error("Failed loading locale file %s: %s", file_path, e)

    def t(self, key: str, lang: str = "en", **kwargs: Any) -> str:
        """Translates a key into the target language with formatting kwargs and English fallback."""
        lang_code = lang.lower() if lang else "en"
        # Fallback to English if language not supported
        if lang_code not in self._translations:
            lang_code = "en"

        text = self._translations.get(lang_code, {}).get(key)
        if text is None:
            # Fallback to English key
            text = self._translations.get("en", {}).get(key, key)

        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

# Global singleton
i18n = I18nService()
