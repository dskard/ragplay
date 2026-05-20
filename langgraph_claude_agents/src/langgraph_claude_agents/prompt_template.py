class PromptTemplate:
    """Format input variables into a prompt string."""

    def __init__(self, template: str) -> None:
        self.template = template

    def format(self, **kwargs: object) -> str:
        return self.template.format(**kwargs)
