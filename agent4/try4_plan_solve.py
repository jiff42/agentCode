from try1_LLMAgent import HelloAgentsLLM

PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题： {question}

请严格按照以下格式输出你的计划，```python与```作为前后缀是必要的：
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

class Planner:
    def __init__(self, llm_client):
        self.llm = llm_client

    def plan(self, question: str) -> list[str]:
        """根据问题生成一个行动计划。"""
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]
        print('--- 正在生成计划 ---')
        response_txt = self.llm_client.think(messages=messages) or ''
        print(f'✅计划已经生成：\n{response_txt}')

        # 解析LLM输出的列表字符串
        try:
            # 找到```python和```之间的内容
            plan_str = response_txt.split('```python')[1].split('```')[0].strip()
            # 使用ast.literal_eval解析列表字符串，转换为Python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else [] 
            

        except (ValueError, syntaxError, IndexError) as e:
            print(f"错误：无法解析计划列表：{e}")
            print(f"原始响应：{response_txt}")
            return []
        except Exception as e:
            print(f"未知错误：{e}")
            print(f"原始响应：{response_txt}")
            return []
