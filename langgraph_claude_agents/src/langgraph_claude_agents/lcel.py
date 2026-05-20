import inspect
from typing import Any, Callable


class Runnable:
    """Base class for LCEL-style composable units."""

    async def ainvoke(self, input: Any) -> Any:
        raise NotImplementedError

    def __or__(self, other: Any) -> "RunnableSequence":
        if not isinstance(other, Runnable):
            other = RunnableLambda(other)
        return RunnableSequence(self, other)


class RunnableLambda(Runnable):
    def __init__(self, fn: Callable[[Any], Any]) -> None:
        self.fn = fn

    async def ainvoke(self, input: Any) -> Any:
        result = self.fn(input)
        if inspect.isawaitable(result):
            result = await result
        return result


class RunnableSequence(Runnable):
    def __init__(self, *steps: Runnable) -> None:
        self.steps: list[Runnable] = []
        for step in steps:
            if isinstance(step, RunnableSequence):
                self.steps.extend(step.steps)
            else:
                self.steps.append(step)

    async def ainvoke(self, input: Any) -> Any:
        value = input
        for step in self.steps:
            value = await step.ainvoke(value)
        return value


class StrOutputParser(Runnable):
    async def ainvoke(self, input: Any) -> str:
        return str(input)
