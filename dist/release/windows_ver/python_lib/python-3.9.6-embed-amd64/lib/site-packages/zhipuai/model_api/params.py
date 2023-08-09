import dataclasses
from typing import Dict, List


@dataclasses.dataclass
class ModelParams:
    model: str = None
    prompt: List[Dict[str, str]] = None
    top_p: float = None
    temperature: float = None

    def asdict(self):
        return dataclasses.asdict(self)
