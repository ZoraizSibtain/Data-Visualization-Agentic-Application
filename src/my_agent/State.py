from typing import TypedDict, Any, List, Optional, Dict, Union

class InputState(TypedDict):
    question: str
    uuid: str

class OutputState(TypedDict):
    answer: str
    visualization: str
    visualization_reason: str
    formatted_data_for_visualization: Dict[str, Any]
    sql_query: str
    results: Any

class AgentState(InputState, OutputState, total=False):
    # Internal state can include intermediate results
    parsed_question: Dict[str, Any]
    unique_nouns: List[str]
    sql_valid: bool
    sql_issues: str
    raw_results: Any
    chart_type: str
    error: str
