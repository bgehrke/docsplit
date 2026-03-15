"""Configuration management for docsplit."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    """Path configuration."""

    inbox: Path
    archive: Path
    processed: Path
    quarantine: Path
    database: Path


class OCRConfig(BaseModel):
    """OCR configuration."""

    dpi: int = Field(default=150, ge=72, le=600)
    language: str = "eng"
    max_pages: int = Field(default=2, ge=1, le=10)
    preprocessing: bool = True  # Enable image preprocessing
    deskew: bool = True  # Correct rotation
    sharpen: bool = True  # Sharpen text
    contrast: bool = True  # Enhance contrast
    denoise: bool = False  # Remove noise (slow)


class MetadataConfig(BaseModel):
    """Metadata extraction configuration."""

    model: str = "mistral"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class SeparatorConfig(BaseModel):
    """Separator detection configuration."""

    text: str = "DOCPROC_SEP"
    fuzzy_threshold: int = Field(default=85, ge=0, le=100)


class WatchConfig(BaseModel):
    """Watch mode configuration."""

    interval: int = Field(default=5, ge=1)
    stability_check: bool = True


class ArchiveRule(BaseModel):
    """Archive routing rule."""

    doc_type: str | None = None  # Match document type
    vendor_contains: str | None = None  # Match vendor name (substring)
    path: str  # Destination path template (e.g., "{year}/tax-documents")
    naming_template: str | None = None  # Custom filename template (e.g., "{tax_form_id}-{vendor}.pdf")


class Config(BaseModel):
    """Main configuration."""

    paths: PathsConfig
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    separator: SeparatorConfig = Field(default_factory=SeparatorConfig)
    watch: WatchConfig = Field(default_factory=WatchConfig)
    archive_rules: list[ArchiveRule] = Field(default_factory=list)


def get_config_path() -> Path:
    """Get the configuration file path."""
    # Check environment variable first
    if env_path := os.getenv("DOCSPLIT_CONFIG"):
        return Path(env_path)

    # XDG config directory
    xdg_config = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    config_path = Path(xdg_config) / "docsplit" / "config.yaml"

    if config_path.exists():
        return config_path

    # Fallback to home directory
    home_config = Path.home() / ".docsplit.yaml"
    if home_config.exists():
        return home_config

    raise FileNotFoundError(
        f"Configuration file not found. "
        f"Create one at {config_path} or set DOCSPLIT_CONFIG environment variable."
    )


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = get_config_path()

    with open(config_path, "r") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    # Expand paths
    if "paths" in data:
        for key, value in data["paths"].items():
            if isinstance(value, str):
                data["paths"][key] = Path(value).expanduser()

    return Config(**data)
