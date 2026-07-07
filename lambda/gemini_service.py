import logging
import os

import google.generativeai as genai

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
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
        )

    def ask(self, question: str, history: list[dict[str, list[str] | str]]) -> str:
        try:
            chat = self._model.start_chat(history=history)
            response = chat.send_message(question)
            text = response.text.strip() if response.text else ""
            if not text:
                return "Desculpe, não consegui formular uma resposta agora."
            return text
        except Exception:
            logger.exception("Erro ao consultar Gemini")
            return "Desculpe, tive um problema ao processar sua pergunta. Tente novamente."
