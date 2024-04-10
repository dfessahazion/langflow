import json
from pathlib import Path
from typing import List, Optional, Union

from dotenv import load_dotenv

from langflow.graph import Graph
from langflow.graph.schema import RunOutputs
from langflow.processing.process import process_tweaks, run_graph
from langflow.utils.logger import configure
from langflow.utils.util import update_settings


def load_flow_from_json(
    flow: Union[Path, str, dict],
    tweaks: Optional[dict] = None,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    env_file: Optional[str] = None,
    cache: Optional[str] = None,
    disable_logs: Optional[bool] = True,
) -> Graph:
    """
    Load a flow graph from a JSON file or a JSON object.

    Args:
        flow (Union[Path, str, dict]): The flow to load. It can be a file path (str or Path object)
            or a JSON object (dict).
        tweaks (Optional[dict]): Optional tweaks to apply to the loaded flow graph.
        log_level (Optional[str]): Optional log level to configure for the flow processing.
        log_file (Optional[str]): Optional log file to configure for the flow processing.
        env_file (Optional[str]): Optional .env file to override environment variables.
        cache (Optional[str]): Optional cache path to update the flow settings.
        disable_logs (Optional[bool], default=True): Optional flag to disable logs during flow processing.
            If log_level or log_file are set, disable_logs is not used.

    Returns:
        Graph: The loaded flow graph as a Graph object.

    Raises:
        TypeError: If the input is neither a file path (str or Path object) nor a JSON object (dict).

    """
    # If input is a file path, load JSON from the file
    configure(log_level=log_level, log_file=log_file, disable=disable_logs)

    # override env variables with .env file
    if env_file:
        load_dotenv(env_file, override=True)

    # Update settings with cache and components path
    update_settings(cache=cache)

    if isinstance(flow, (str, Path)):
        with open(flow, "r", encoding="utf-8") as f:
            flow_graph = json.load(f)
    # If input is a dictionary, assume it's a JSON object
    elif isinstance(flow, dict):
        flow_graph = flow
    else:
        raise TypeError("Input must be either a file path (str) or a JSON object (dict)")

    graph_data = flow_graph["data"]
    if tweaks is not None:
        graph_data = process_tweaks(graph_data, tweaks)

    graph = Graph.from_payload(graph_data)
    return graph


def run_flow_from_json(
    flow: Union[Path, str, dict],
    input_value: str,
    tweaks: Optional[dict] = None,
    input_type: str = "chat",
    output_type: str = "chat",
    output_component: Optional[str] = None,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    env_file: Optional[str] = None,
    cache: Optional[str] = None,
    disable_logs: Optional[bool] = True,
) -> List[RunOutputs]:
    # Set all streaming to false
    if tweaks is None:
        tweaks = {}
    tweaks["stream"] = False
    graph = load_flow_from_json(
        flow=flow,
        tweaks=tweaks,
        log_level=log_level,
        log_file=log_file,
        env_file=env_file,
        cache=cache,
        disable_logs=disable_logs,
    )
    result = run_graph(
        graph=graph,
        input_value=input_value,
        input_type=input_type,
        output_type=output_type,
        output_component=output_component,
    )
    return result
