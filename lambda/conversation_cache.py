from collections import deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class ConversationTurn:
    question: str
    answer: str


class ConversationCache:
    def __init__(self, max_turns: int = 20) -> None:
        self._max_turns = max_turns
        self._store: dict[str, deque[ConversationTurn]] = {}
        self._lock = Lock()

    def get_history(self, session_id: str) -> list[ConversationTurn]:
        with self._lock:
            turns = self._store.get(session_id)
            if not turns:
                return []
            return list(turns)

    def add_turn(self, session_id: str, question: str, answer: str) -> None:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self._max_turns)
            self._store[session_id].append(ConversationTurn(question=question, answer=answer))

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def to_gemini_history(self, session_id: str) -> list[dict[str, list[str] | str]]:
        history: list[dict[str, list[str] | str]] = []
        for turn in self.get_history(session_id):
            history.append({"role": "user", "parts": [turn.question]})
            history.append({"role": "model", "parts": [turn.answer]})
        return history
