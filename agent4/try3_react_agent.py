import re
from difflib import get_close_matches
from try1_LLMAgent import HelloAgentsLLM
from try2_react_tools import ToolExecutor, search, calculator

REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：

{tools}

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。

Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`: 调用一个可用工具。
- `Finish[最终答案]`: 当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action: 字段后使用 Finish[最终答案] 来输出最终答案。
- 每次回复只能包含一个 Thought 和一个 Action，不要一次输出多个 Action。
- 调用工具后必须等待 History 中出现 observation，再决定下一步。

现在，请开始解决以下问题：
Question: {question}
History: {history}
"""

class ReactAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor,
    max_steps: int=5, max_tool_failures: int=3):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.max_tool_failures = max_tool_failures
        self.history = []
        
    def run(self, question: str):
        """
        运行ReACT智能体，回答一个问题。
        """
        self.history = []     # 每次运行时充值历史记录
        current_step = 0
        consecutive_tool_failures = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f'--- 第{current_step}步 ---')

            # 1. 格式化提示词
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                history=history_str
            )

            # 2. 调用LLM进行思考
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages)

            if not response_text:
                print("⚠️LLM返回空响应，无法继续。")
                break

            thought, action = self._parse_output(response_text)

            if thought:
                print(f"🤔思考: {thought}")

            if not action:
                observation = self._build_tool_correction(
                    "missing_action",
                    response_text,
                    None,
                    None
                )
                consecutive_tool_failures += 1
                print(f"👀 观察: {observation}")
                self.history.append(f"Action: {response_text}")
                self.history.append(f"observation: {observation}")
                if consecutive_tool_failures >= self.max_tool_failures:
                    print("工具选择或参数连续失败次数过多，流程终止。")
                    return None
                continue

            if action.startswith("Finish"):
                match = re.match(r"^Finish\[(.*)\]$", action, re.DOTALL)
                final_answer = match.group(1) if match else action
                print(f"✅ 最终答案: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or tool_input is None or tool_input == "":
                observation = self._build_tool_correction(
                    "invalid_action_format",
                    action,
                    tool_name,
                    tool_input
                )
                consecutive_tool_failures += 1
                print(f"👀 观察: {observation}")
                self.history.append(f"Action: {action}")
                self.history.append(f"observation: {observation}")
                if consecutive_tool_failures >= self.max_tool_failures:
                    print("工具选择或参数连续失败次数过多，流程终止。")
                    return None
                continue

            print(f"🛠 行动: {tool_name}[{tool_input}]")

            tool_function = self.tool_executor.getTool(tool_name)
            if not tool_function:
                observation = self._build_tool_correction(
                    "unknown_tool",
                    action,
                    tool_name,
                    tool_input
                )
                consecutive_tool_failures += 1
                print(f"👀 观察: {observation}")
                self.history.append(f"Action: {action}")
                self.history.append(f"observation: {observation}")
                if consecutive_tool_failures >= self.max_tool_failures:
                    print("工具选择或参数连续失败次数过多，流程终止。")
                    return None
                continue
            else:
                try:
                    observation = tool_function(tool_input)
                except Exception as e:
                    observation = f"工具执行异常：{e}"

            print(f"👀 观察: {observation}")
            self.history.append(f"Action: {action}")
            self.history.append(f"observation: {observation}")
            if self._is_tool_failure(observation):
                correction = self._build_tool_correction(
                    "tool_execution_error",
                    action,
                    tool_name,
                    tool_input,
                    observation
                )
                consecutive_tool_failures += 1
                print(f"🔁 纠偏提示: {correction}")
                self.history.append(f"observation: {correction}")
                if consecutive_tool_failures >= self.max_tool_failures:
                    print("工具选择或参数连续失败次数过多，流程终止。")
                    return None
            else:
                consecutive_tool_failures = 0

        print("已达到最大步数，流程终止。")
        return None

    def _parse_output(self, text: str):
        """解析LLM的输出，提取Thought和Action。"""
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        action_match = re.search(r"Action:\s*([^\n\r]*)", text)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """解析Action字符串，提取工具名称和输入。"""
        match = re.match(r"^(\w+)\[(.*)\]$", action_text.strip())
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _is_tool_failure(self, observation: str) -> bool:
        failure_prefixes = (
            "错误",
            "计算错误",
            "搜索过程中出现错误",
            "工具执行异常",
        )
        return observation.strip().startswith(failure_prefixes)

    def _build_tool_correction(
        self,
        failure_type: str,
        action: str,
        tool_name: str | None,
        tool_input: str | None,
        error_detail: str | None = None
    ) -> str:
        available_tools = list(self.tool_executor.tools.keys())
        tools_text = ", ".join(available_tools)
        correction = [
            "工具调用失败。下一步必须先根据失败原因修正 Action，不要重复同样的调用。",
            f"可用工具名称只能从这些值中选择: {tools_text}。",
            "合法格式只能是 ToolName[参数] 或 Finish[最终答案]。",
        ]

        if failure_type == "missing_action":
            correction.append("失败原因: 回复中缺少 Action 字段。")
        elif failure_type == "invalid_action_format":
            correction.append(f"失败原因: Action 格式无效，当前 Action 是: {action}。")
        elif failure_type == "unknown_tool":
            correction.append(f"失败原因: 工具 '{tool_name}' 不存在。")
            suggested_tool = self._suggest_tool_name(tool_name, available_tools)
            if suggested_tool:
                correction.append(f"你可能想使用的工具是: {suggested_tool}。")
        elif failure_type == "tool_execution_error":
            correction.append(f"失败原因: 工具执行返回错误: {error_detail}。")
            if tool_name == "Calculator":
                correction.append("Calculator 的参数应该是纯数学表达式，例如 Calculator[(123 + 456) * 789 / 12]。")
            elif tool_name == "Search":
                correction.append("Search 的参数应该是用于网页搜索的关键词或问题。")

        if tool_input == "":
            correction.append("失败原因: 工具参数为空，必须提供非空参数。")

        return " ".join(correction)

    def _suggest_tool_name(self, tool_name: str | None, available_tools: list[str]) -> str | None:
        if not tool_name:
            return None
        matches = get_close_matches(tool_name, available_tools, n=1, cutoff=0.5)
        return matches[0] if matches else None


if __name__ == "__main__":
    llm = HelloAgentsLLM()
    toolExecutor = ToolExecutor()

    # 注册工具 -- 网页搜索
    search_description = (
        "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    )
    toolExecutor.registerTool("Search", search_description, search)

    # 注册工具 -- 计算器
    calculator_description = "一个计算器工具，当你需要进行简单的数学计算时如'532+25*12'，应当使用此工具。"
    toolExecutor.registerTool('Calculator',calculator_description, calculator)

    agent = ReactAgent(llm, toolExecutor)
    question = "我正在学习数学的加减乘除，帮我计算一下(123 +456) × 789/ 12 等于多少，我已经计算了，我需要对一下答案"
    answer = agent.run(question)
    print(answer)


