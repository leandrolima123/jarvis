import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é o Jarvis, um assistente de voz para Alexa. "
    "Responda sempre em português do Brasil. "
    "Seja conciso: no máximo duas ou três frases curtas. "
    "Não use markdown, listas, emojis ou formatação especial. "
    "Fale de forma natural, como se estivesse conversando por voz."
)


class GeminiService:
    def __init__(self) -> None:
        api_key = os.environ["GEMINI_API_KEY"]
        self._model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = genai.Client(api_key=api_key)
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=256,
            temperature=0.7,
        )

    def _build_history(
        self, history: list[dict[str, list[str] | str]]
    ) -> list[types.Content]:
        contents: list[types.Content] = []
        for item in history:
            role = item.get("role")
            parts = item.get("parts") or []
            text = parts[0] if parts else ""
            if not text:
                continue
            if role == "user":
                contents.append(types.UserContent(parts=[types.Part.from_text(text=str(text))]))
            elif role == "model":
                contents.append(types.ModelContent(parts=[types.Part.from_text(text=str(text))]))
        return contents

    def ask(self, question: str, history: list[dict[str, list[str] | str]]) -> str:
        try:
            chat = self._client.chats.create(
                model=self._model_name,
                config=self._config,
                history=self._build_history(history),
            )
            response = chat.send_message(question)
            text = response.text.strip() if response.text else ""
            if not text:
                return "Desculpe, não consegui formular uma resposta agora."
            return text
        except Exception:
            logger.exception("Erro ao consultar Gemini")
            return "Desculpe, tive um problema ao processar sua pergunta. Tente novamente."
