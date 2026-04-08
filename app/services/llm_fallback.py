import re
from typing import List, Dict

class LlmFallback:
    """
    Static rules for analysis and summarization when LLMs are unavailable.
    """
    def summarize(self, all_responses: List[str]) -> dict:
        total_words = sum(len(r.split()) for r in all_responses)
        summary = f"Recebemos {len(all_responses)} feedbacks de texto totalizando cerca de {total_words} palavras. "
        
        positives = []
        negatives = []
        
        # Simple heuristic keywords
        pos_words = ["bom", "ótimo", "excelente", "gostei", "claro", "didático", "útil"]
        neg_words = ["ruim", "péssimo", "confuso", "rápido", "devagar", "faltou", "exemplo"]
        
        for r in all_responses:
            lower_r = r.lower()
            if any(w in lower_r for w in pos_words):
                if len(positives) < 3: positives.append(r[:100] + "...")
            if any(w in lower_r for w in neg_words):
                if len(negatives) < 3: negatives.append(r[:100] + "...")
                
        return {
            "summary": summary + "A análise sem IA se baseia em contagem de palavras-chave simples.",
            "positives": positives if positives else ["Nenhum elogio explícito detectado pela regra estática."],
            "negatives": negatives if negatives else ["Nenhuma crítica explícita detectada pela regra estática."],
            "recommendations": ["Aprofunde os assuntos mais comentados.", "Verifique se a duração da sessão foi adequada."]
        }
        
    def classify_theme(self, text: str) -> List[Dict]:
        text = text.lower()
        themes = []
        
        # Static taxonomy
        if "tempo" in text or "rápido" in text or "longo" in text:
            themes.append({"theme_name": "Gestão de Tempo", "sentiment": "neutral", "confidence": 0.5})
        if "claro" in text or "entendi" in text or "confuso" in text:
            themes.append({"theme_name": "Clareza", "sentiment": "neutral", "confidence": 0.5})
        if "exemplo" in text or "prático" in text or "dia a dia" in text:
            themes.append({"theme_name": "Aplicabilidade Prática", "sentiment": "neutral", "confidence": 0.5})
            
        if not themes:
            themes.append({"theme_name": "Geral", "sentiment": "neutral", "confidence": 0.3})
            
        return themes

llm_fallback = LlmFallback()
