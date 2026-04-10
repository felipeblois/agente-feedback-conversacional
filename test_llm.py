import asyncio

from app.services.llm_client import call_llm


async def main():
    print("Testando conexao com a estrategia cloud de LLM...")
    prompt = "Responda apenas com a palavra: CONECTADO"

    try:
        response = await call_llm(prompt)
        print("--- RESPOSTA RECEBIDA ---")
        print(response)

        if response and "CONECTADO" in response.upper():
            print("\nSUCESSO: Um dos provedores cloud respondeu corretamente.")
        else:
            print("\nAVISO: A resposta veio vazia e o fluxo caiu no fallback local.")
    except Exception as exc:
        print(f"\nERRO: Falha ao chamar a API: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
