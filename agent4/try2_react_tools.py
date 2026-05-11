import os
from serpapi import SerpApiClient
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

def search(query: str) -> str:
    """
    一个基于SerpAp的实战网页搜索引擎工具。
    会智能第解析搜索解雇，优先返回直接答案或知识图谱信息。
    """
    print(f"***** 正在执行 [SerpAPI] 网页搜索: {query} *****")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：未在.env中配置SERPAPI_API_KEY"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",        # 搜索区域，cn=中国
            "hl": "zh-cn",     # 界面语言，zh-cn=简体中文
        }
        client = SerpApiClient(params)
        results = client.get_dict()

        # 智能解析，优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]: 
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title','')}\n{res.get('snippet','')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        return f"抱歉，没找到关于'{query}'的相关的信息。请尝试使用其他关键词搜索。"
    except Exception as e:
        return f"搜索过程中出现错误: {e}"
    
        
class ToolExecutor:
    """
    一个工具执行器，复制管理和执行工具。
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        向工具箱中注册一个新工具
        """
        if name in self.tools:
            print(f"⚠️警告: 工具'{name}'已经存在，将被覆盖。")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具'{name}'已经注册。")

    def getTool(self, name: str) -> callable:
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])


# ***** 工具初始化与使用示例 *****
if __name__ == '__main__':
    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册实战搜索工具
    search_description = "一个网页搜搜引擎。当需要回答关于时事、事实以及在知识库中找不到信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)

    # 3. 打印可用的工具
    print("\n***** 可用的工具 *****")
    print(toolExecutor.getAvailableTools())

    # 4. 智能体的Action调用
    print("\n***** 执行Action: Search['英伟达最新GPU的型号是什么，具体信息是什么'] *****")
    tool_name = "Search"
    tool_input = "英伟达最新GPU的型号是什么，具体信息是什么"
    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("***** 观察(observation) *****")
        print(observation)
    else:
        print(f"错误：未找到名为'{tool_name}'的工具。")

        
        
        
        

        