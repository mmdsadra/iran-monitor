from dataclasses import dataclass
import os


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    def __repr__(self) -> str:
        return (
            "LLMConfig("
            "api_key='**********', "
            f"base_url={self.base_url!r}, "
            f"model={self.model!r}, "
            f"timeout={self.timeout!r}"
            ")"
        )

    @classmethod
    def from_environment(cls) -> "LLMConfig":
        api_key = os.getenv("IRAN_MONITOR_LLM_API_KEY")

        if not api_key:
            raise RuntimeError(
                "IRAN_MONITOR_LLM_API_KEY is not configured"
            )

        return cls(
            api_key=api_key,
            base_url=os.getenv(
                "IRAN_MONITOR_LLM_BASE_URL",
                "https://api.openai.com/v1",
            ),
            model=os.getenv(
                "IRAN_MONITOR_LLM_MODEL",
                "gpt-4o-mini",
            ),
            timeout=float(
                os.getenv(
                    "IRAN_MONITOR_LLM_TIMEOUT",
                    "30",
                )
            ),
        )