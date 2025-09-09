import base64
from datetime import datetime
import json
import logging
from typing import Literal, Optional, Union, Callable, Any, Set
from pathlib import Path

logger = logging.getLogger(__name__)


def get_current_datetime(format: Optional[str] = None) -> str:
    """
    Get the current time as a JSON string, optionally formatted.

    Args:
        format (Optional[str]): The format in which to return the current time. Defaults to None, which uses a standard format.

    Returns:
        str: The current time in JSON format.
    """
    current_time = datetime.now()

    if format:
        time_format = format
    else:
        time_format = "%Y-%m-%d %H:%M:%S"

    time_json = json.dumps({"current_time": current_time.strftime(time_format)})
    return time_json


def load_image_from_file(
    file_path: str,
    return_format: Literal["bytes", "base64"] = "base64"
) -> Union[bytes, str]:
    """
    Load an image from a local file.

    Args:
        file_path (str): Path to the local image file.
        return_format (Literal): Format of return ("bytes", "base64").

    Returns:
        Union[bytes, str]: Image data in the requested format.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        data = f.read()

    if return_format == "bytes":
        return data
    elif return_format == "base64":
        return base64.b64encode(data).decode("utf-8")
    else:
        raise ValueError(f"Unsupported return_format: {return_format}")

# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {
    load_image_from_file,
    get_current_datetime
}
