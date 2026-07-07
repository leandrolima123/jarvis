import logging
import os

from conversation_cache import ConversationCache
from gemini_service import GeminiService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

WELCOME_MESSAGE = "Olá, sou o Jarvis. O que você quer saber?"
FALLBACK_MESSAGE = "Não entendi sua pergunta. Pode repetir?"
STOP_MESSAGE = "Até logo. Estou aqui quando precisar."
HELP_MESSAGE = (
    "Você pode me fazer perguntas sobre qualquer assunto. "
    "Por exemplo: o que é inteligência artificial?"
)

AVAILABILITY_CHECK_USER = "alexa-lambda-availability"

_cache: ConversationCache | None = None
_gemini: GeminiService | None = None


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


def build_response(text: str, should_end_session: bool = False) -> dict:
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


def _extract_question(event: dict) -> str | None:
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
    request_type = _request_type(event)
    session_id = _session_id(event)

    logger.info("Request type: %s session: %s", request_type, session_id)

    if request_type == "LaunchRequest":
        if _user_id(event) == AVAILABILITY_CHECK_USER:
            return build_response("")
        return build_response(WELCOME_MESSAGE)

    cache = _get_cache()

    if request_type == "SessionEndedRequest":
        cache.clear(session_id)
        return build_response("", should_end_session=True)

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
