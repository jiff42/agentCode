import os
from serpapi import SerpApiClient

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
            " serpapi_api_key": api_key,
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
    
        
        # 

        
        
        
        

        