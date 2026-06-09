from langchain_openai import OpenAIEmbeddings


def get_embedder(model: str, api_key: str) -> OpenAIEmbeddings:
    """返回 OpenAI Embedding 模型实例（兼容 Ollama 可替换 base_url）。"""
    # TODO: 阶段二实现 — 支持 Ollama base_url 切换
    return OpenAIEmbeddings(model=model, api_key=api_key)
