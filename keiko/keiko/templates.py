"""Module to extract template definitions from reports directory."""

import importlib
import importlib.machinery
import importlib.util
import json
import os
from logging import getLogger
from pathlib import Path
from typing import Set, Any, Dict, cast

from pydantic import BaseModel

from keiko.settings import Settings

DATA_STRUCTURE_MODULE_NAME = "model.py"
DATA_STRUCTURE_CLASS_NAME = "DataShape"

logger = getLogger(__name__)


def get_templates(settings: Settings) -> Set[str]:
    """Assembles all template definitions found in the templates directory."""

    templates = set()

    for template_folder in [
        f for f in os.listdir(settings.templates_folder) if (Path(settings.templates_folder) / f).is_dir()
    ]:
        try:
            get_data_shape(template_folder, settings)
            templates.add(template_folder)
        except FileNotFoundError:
            logger.warning(
                "Template data shape definition not found. [template=%s]",
                template_folder,
            )

    return templates


def get_data_shape(template: str, settings: Settings) -> BaseModel:
    """Imports the data model for a template"""

    model_path = Path(settings.templates_folder) / template / DATA_STRUCTURE_MODULE_NAME

    #
    # The following routine loads a python file, which is not part of a reachable python module in 'the usual way'
    #
    loader = importlib.machinery.SourceFileLoader(f"{template}_model", str(model_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise FileNotFoundError(
            f"No such file or directory: {model_path}",
        )
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)

    return cast(BaseModel, getattr(module, DATA_STRUCTURE_CLASS_NAME))


def get_samples(settings: Settings) -> Dict[str, Dict[str, Any]]:
    """Returns a dictionary of sample data for each template"""
    samples = {}
    template_folder = Path(settings.templates_folder)
    logger.info("Loading samples in folder: %s", template_folder.absolute())

    for subfolder_name in os.listdir(template_folder.absolute()):
        subfolder = template_folder / subfolder_name
        if not subfolder.is_dir():
            continue
        sample_file = subfolder / "sample.json"
        if sample_file.exists():
            with open(sample_file) as sample:
                try:
                    samples[subfolder_name] = {
                        "summary": subfolder_name,
                        "value": json.load(sample),
                    }
                except json.decoder.JSONDecodeError:
                    logger.warning(
                        "Could not load sample data for template %s. Invalid JSON",
                        subfolder_name,
                    )

    return samples
