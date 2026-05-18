import os
from typing import Any, Callable, Dict
from serpapi import SerpApiClient
from dotenv import load_dotenv
import operator
import ast

load_dotenv()  # 加载环境变量


class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: Callable[..., Any]):
        """
        向工具箱中注册一个新工具。
        """
        if name in self.tools:
            print(f"警告:工具 '{name}' 已存在，将被覆盖。")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> Callable[..., Any] | None:
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join(
            [f"- {name}: {info['description']}" for name, info in self.tools.items()]
        )


def search(query: str) -> str:
    """
    一个基于 SerpApi 的实战网页搜索引擎工具。
    会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"***** 正在执行 [SerpAPI] 网页搜索: {query} *****")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：SERPAPI_API_KEY 未在 .env 文件中配置。"

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



def calculator(expression: str) -> str:
    """
    一个简单的计算器，用于数学公式的计算。
    参数: expression - 字符串形式的数学表达式，例如 "2 + 3 * 4"
    
    返回: 计算结果
    """
    print(f'--- 正在执行工具 [calculator] 计算{expression} ---')

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
 
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
 
        if isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_type = type(node.op)
 
            if op_type not in operators:
                raise ValueError(f"不支持的运算符: {op_type.__name__}")
 
            return operators[op_type](left, right)
 
        if isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            op_type = type(node.op)
 
            if op_type not in operators:
                raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
 
            return operators[op_type](operand)
 
        raise ValueError("表达式中包含不支持的内容，只允许数字和数学运算符。")
 
    try:
        normalized_expression = (
            expression
            .replace("×", "*")
            .replace("÷", "/")
            .replace("＝", "=")
            .replace("？", "")
            .replace("?", "")
            .strip()
        )
 
        if "=" in normalized_expression:
            normalized_expression = normalized_expression.split("=")[0].strip()
 
        tree = ast.parse(normalized_expression, mode="eval")
        result = eval_node(tree)
 
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "计算错误：除数不能为 0。"
    except Exception as e:
        return f"计算错误：{e}"




if __name__ == "__main__":
    toolExecutor = ToolExecutor()

    search_description = (
        "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    )
    toolExecutor.registerTool("Search", search_description, search)

    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    print("\n--- 执行 Action: Search['英伟达/NVIDIA最新的GPU型号是什么？'] ---")
    tool_name = "Search"
    tool_input = "英伟达/NVIDIA最新的GPU型号是什么？"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误:未找到名为 '{tool_name}' 的工具。")


