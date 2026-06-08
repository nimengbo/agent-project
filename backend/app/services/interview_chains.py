from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.services.deepseek_service import deepseek_service


class BaseInterviewChain:
    def __init__(self, prompt: ChatPromptTemplate, use_reasoner: bool = False, temperature: float = 0.4) -> None:
        self.prompt = prompt
        self.use_reasoner = use_reasoner
        self.temperature = temperature
        self.parser = StrOutputParser()

    async def ainvoke(self, values: dict[str, Any]) -> str:
        prompt_value = self.prompt.invoke(values)
        role_map = {"human": "user", "ai": "assistant", "system": "system"}
        messages = [
            {"role": role_map.get(message.type, message.type), "content": str(message.content)}
            for message in prompt_value.to_messages()
        ]
        content = await deepseek_service.chat(
            messages,
            use_reasoner=self.use_reasoner,
            temperature=self.temperature,
        )
        return self.parser.invoke(content).strip()


class QuestionChain(BaseInterviewChain):
    def __init__(self) -> None:
        super().__init__(
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "你是一名资深技术面试官，正在为候选人进行中文模拟面试。"
                        "每轮只问一个具体、可回答的问题，不输出参考答案。"
                        "问题需要贴合目标岗位、难度和候选人资料。"
                        "严禁重复已问过的问题；如果同一主题已经问过，必须换一个角度继续追问。",
                    ),
                    (
                        "human",
                        "目标岗位：{position}\n难度：{difficulty}\n候选人资料：{candidate_profile}\n"
                        "已问过的问题：{asked_questions}\n"
                        "已进行的对话：{conversation}\n请给出下一道面试问题。",
                    ),
                ]
            ),
            temperature=0.45,
        )

    async def generate(
        self,
        content: str,
        position: str,
        difficulty: str,
        candidate_profile: str = "暂无",
        conversation: str = "暂无",
        asked_questions: str = "暂无",
    ) -> str:
        return await self.ainvoke(
            {
                "position": position,
                "difficulty": difficulty,
                "candidate_profile": candidate_profile,
                "conversation": f"{conversation}\n候选人最新输入：{content}",
                "asked_questions": asked_questions,
            }
        )


class FollowupChain(BaseInterviewChain):
    def __init__(self) -> None:
        super().__init__(
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "你是一名会深挖项目细节的技术面试官。"
                        "根据候选人回答生成一个追问，优先追问架构取舍、边界条件、数据指标或故障复盘。",
                    ),
                    (
                        "human",
                        "原问题：{question}\n候选人回答：{answer}\n岗位：{position}\n难度：{difficulty}\n请生成一个追问。",
                    ),
                ]
            ),
            use_reasoner=True,
            temperature=0.35,
        )

    async def generate(
        self,
        question: str,
        answer: str,
        position: str,
        difficulty: str,
        candidate_profile: str = "暂无",
    ) -> str:
        return await self.ainvoke(
            {
                "question": question,
                "answer": f"{answer}\n\n候选人资料/RAG：{candidate_profile}",
                "position": position,
                "difficulty": difficulty,
            }
        )


class AnswerReviewChain(BaseInterviewChain):
    def __init__(self) -> None:
        super().__init__(
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "你是一名技术面试复盘教练。用中文评价候选人的回答，"
                        "给出分数、亮点、风险点和下一步改进建议。",
                    ),
                    (
                        "human",
                        "岗位：{position}\n难度：{difficulty}\n问题：{question}\n候选人回答：{answer}\n"
                        "请按以下结构输出：总评、评分、亮点、问题、改进建议。",
                    ),
                ]
            ),
            use_reasoner=True,
            temperature=0.25,
        )

    async def review(
        self,
        question: str,
        answer: str,
        position: str,
        difficulty: str,
        candidate_profile: str = "暂无",
    ) -> str:
        return await self.ainvoke(
            {
                "question": question,
                "answer": f"{answer}\n\n候选人资料/RAG：{candidate_profile}",
                "position": position,
                "difficulty": difficulty,
            }
        )


class ReportChain(BaseInterviewChain):
    def __init__(self) -> None:
        super().__init__(
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "你是一名面试报告生成器。基于完整对话生成结构化中文复盘，"
                        "覆盖技术准确性、沟通表达、项目深度、岗位匹配和训练计划。",
                    ),
                    (
                        "human",
                        "岗位：{position}\n难度：{difficulty}\n完整对话：{conversation}\n"
                        "请输出一份可直接给候选人阅读的面试复盘报告。",
                    ),
                ]
            ),
            use_reasoner=True,
            temperature=0.3,
        )

    async def generate(self, conversation: str, position: str, difficulty: str) -> str:
        return await self.ainvoke(
            {"conversation": conversation, "position": position, "difficulty": difficulty}
        )


question_chain = QuestionChain()
followup_chain = FollowupChain()
answer_review_chain = AnswerReviewChain()
report_chain = ReportChain()