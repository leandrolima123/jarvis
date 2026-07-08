from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

WELCOME_MESSAGE = "Olá, sou o Jarvis. O que você quer saber?"
FALLBACK_MESSAGE = "Não entendi sua pergunta. Pode repetir?"
STOP_MESSAGE = "Até logo. Estou aqui quando precisar."
HELP_MESSAGE = (
    "Você pode me fazer perguntas sobre qualquer assunto. "
    "Por exemplo: o que é inteligência artificial?"
)
SYSTEM_PROMPT = (
    "Você é o Jarvis, um assistente de voz para Alexa. "
    "Responda sempre em português do Brasil. "
    "Seja conciso: no máximo duas ou três frases curtas. "
    "Não use markdown, listas, emojis ou formatação especial. "
    "Fale de forma natural, como se estivesse conversando por voz."
)
AVAILABILITY_CHECK_USER = "alexa-lambda-availability"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _load_env_file() -> None:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _get_gemini_api_key() -> str:
    _load_env_file()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY")
    return api_key


_load_env_file()


@dataclass(frozen=True)
class ConversationTurn:
    question: str
    answer: str


class ConversationCache:
    def __init__(self, max_turns: int = 20) -> None:
        self._max_turns = max_turns
        self._store: Dict[str, deque] = {}
        self._lock = Lock()

    def add_turn(self, session_id: str, question: str, answer: str) -> None:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self._max_turns)
            self._store[session_id].append(ConversationTurn(question=question, answer=answer))

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def to_gemini_history(self, session_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            turns = self._store.get(session_id)
            if not turns:
                return []

        history: List[Dict[str, Any]] = []
        for turn in turns:
            history.append({"role": "user", "parts": [{"text": turn.question}]})
            history.append({"role": "model", "parts": [{"text": turn.answer}]})
        return history


class GeminiService:
    def __init__(self) -> None:
        self._api_key = _get_gemini_api_key()
        self._model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def _build_contents(
        self, question: str, history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        contents = list(history)
        contents.append({"role": "user", "parts": [{"text": question}]})
        return contents

    def ask(self, question: str, history: List[Dict[str, Any]]) -> str:
        try:
            url = GEMINI_API_URL.format(model=self._model_name)
            url = "{0}?key={1}".format(url, self._api_key)
            payload = {
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": self._build_contents(question, history),
                "generationConfig": {
                    "maxOutputTokens": 256,
                    "temperature": 0.7,
                },
            }
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))

            candidates = body.get("candidates") or []
            if not candidates:
                return "Desculpe, não consegui formular uma resposta agora."

            parts = candidates[0].get("content", {}).get("parts") or []
            text_parts = [part.get("text", "") for part in parts if part.get("text")]
            text = " ".join(text_parts).strip()
            if not text:
                return "Desculpe, não consegui formular uma resposta agora."
            return text
        except KeyError:
            logger.exception("Chave Gemini nao configurada")
            return "Desculpe, a chave da API nao foi configurada. Crie o arquivo env na pasta lambda."
        except urllib.error.HTTPError as exc:
            logger.exception("Erro HTTP Gemini: %s", exc.read().decode("utf-8", errors="ignore"))
            return "Desculpe, tive um problema ao processar sua pergunta. Tente novamente."
        except Exception:
            logger.exception("Erro ao consultar Gemini")
            return "Desculpe, tive um problema ao processar sua pergunta. Tente novamente."


_cache: Optional[ConversationCache] = None
_gemini: Optional[GeminiService] = None


def _get_cache() -> ConversationCache:
    global _cache
    if _cache is None:
        max_turns = int(os.getenv("MAX_HISTORY_TURNS", "20"))
        _cache = ConversationCache(max_turns=max_turns)
    return _cache


def _get_gemini() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini


def build_response(text: str, should_end_session: bool = False) -> Dict[str, Any]:
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": text},
            "shouldEndSession": should_end_session,
        },
    }


def _session_id(event: dict) -> str:
    session = event.get("session") or {}
    return session.get("sessionId", "default")


def _request_type(event: dict) -> str:
    return event.get("request", {}).get("type", "")


def _user_id(event: dict) -> str:
    session = event.get("session") or {}
    user = session.get("user") or {}
    return user.get("userId", "")


def _extract_question(event: dict) -> Optional[str]:
    intent = event.get("request", {}).get("intent")
    if not intent:
        return None

    intent_name = intent.get("name", "")
    if intent_name in {"AMAZON.StopIntent", "AMAZON.HelpIntent"}:
        return None

    slots = intent.get("slots") or {}
    question_slot = slots.get("question") or {}
    question_value = question_slot.get("value")
    if question_value:
        return question_value.strip()

    for slot in slots.values():
        value = slot.get("value")
        if value:
            return value.strip()

    return None


def lambda_handler(event, context):
    try:
        return _handle_request(event)
    except Exception:
        logger.exception("Erro nao tratado no lambda_handler")
        return build_response(
            "Desculpe, ocorreu um erro interno. Verifique os logs e tente novamente."
        )


def _handle_request(event):
    request_type = _request_type(event)
    session_id = _session_id(event)

    logger.info("Request type: %s session: %s", request_type, session_id)

    if request_type == "LaunchRequest":
        if _user_id(event) == AVAILABILITY_CHECK_USER:
            return build_response("ok")
        return build_response(WELCOME_MESSAGE)

    cache = _get_cache()

    if request_type == "SessionEndedRequest":
        cache.clear(session_id)
        return build_response("Até logo.", should_end_session=True)

    if request_type != "IntentRequest":
        return build_response(FALLBACK_MESSAGE)

    intent = event.get("request", {}).get("intent") or {}
    intent_name = intent.get("name", "")

    if intent_name == "AMAZON.StopIntent":
        cache.clear(session_id)
        return build_response(STOP_MESSAGE, should_end_session=True)

    if intent_name == "AMAZON.HelpIntent":
        return build_response(HELP_MESSAGE)

    question = _extract_question(event)
    if not question:
        return build_response(FALLBACK_MESSAGE)

    history = cache.to_gemini_history(session_id)
    answer = _get_gemini().ask(question, history)
    cache.add_turn(session_id, question, answer)

    return build_response(answer)
