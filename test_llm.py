import asyncio
from app.services.llm_client import call_llm

async def main():
    print("Testando conexão com o LLM Principal...")
    prompt = "Responda apenas com a palavra: CONECTADO"
    
    try:
        response = await call_llm(prompt)
        print("--- RESPOSTA RECEBIDA ---")
        print(response)
        
        if response and "CONECTADO" in response.upper():
            print("\n✅ SUCESSO: O Gemini respondeu perfeitamente!")
        else:
            print("\n⚠️ AVISO: A resposta veio vazia ou o modelo de Fallback fixo retornou Null.")
    except Exception as e:
        print(f"\n❌ ERRO: Falha ao chamar a API: {e}")

if __name__ == "__main__":
    asyncio.run(main())
