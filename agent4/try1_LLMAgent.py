import os
from openai import OpenAI
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from typing import Dict, List

# 加载 .env 文件中的环境变量
load_dotenv()

class HelloAgentsLLM:
    """
    用于调用任何兼容的服务，并默认使用流式响应
    """
    def __init__(self, model: str=None, api_key: str=None,
                 base_url: str=None, timeout: int=None):
        """
        初始化LLM客户端。
        优先使用传入的参数；如果没有传入，则尝试从环境变量中获取。
        """
        self.model = model or os.getenv("LLM_MODEL_ID_1")
        self.api_key = api_key or os.getenv("LLM_API_KEY_1")
        self.base_url = base_url or os.getenv("LLM_BASE_URL_1")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not self.model:
            raise ValueError("必须指定模型ID(LLM_MODEL_ID)或在.env中配置")
        if not self.api_key:
            raise ValueError("必须指定API密钥(LLM_API_KEY)或在.env中配置")
        if not self.base_url:
            raise ValueError("必须指定基础URL(LLM_BASE_URL)或在.env中配置")
        
        # 创建OpenAI客户端实例
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    def think(self, messages: List[Dict[str, str]], temperature: float=0) -> str:
        """
        调用大语言模型进行思考，并返回其响应
        """
        print(f"--- 正在调用{self.model}模型... ---")
        try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream = True,
                )

                print(f"--- 大语言模型响应成功: ---")
                collected_content = []
                for chunk in response:
                    content = chunk.choices[0].delta.content or ""
                    print(content,end="",flush=True)
                    collected_content.append(content)
                
                print()  # 在流式输出结束后换行
                return "".join(collected_content)
        except Exception as e:
            print(f"--- 调用大语言模型失败: {e} ---")
            return None

# --- LLM 客户端使用示例 ---
if __name__ == "__main__":
    try:
        llmClinet = HelloAgentsLLM()

        example_messages = [
            {"role": "system", "content": "You are helpful assitant."},
            {"role": "user", "content": "just say: Hello, nice to meet you. I'm here waiting for you."}
        ]

        print("--- 调用LLM ---")
        responseText = llmClinet.think(example_messages)
        # if  responseText:
        #     print("\n--- LLM 响应 ---")
        #     print(responseText)
    except ValueError as e:
        print(f"配置错误: {e}")
    