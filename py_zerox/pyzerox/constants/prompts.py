class Prompts:
    """Class for storing prompts for the Zerox system."""

    DEFAULT_SYSTEM_PROMPT = """
    Convert the following PDF page to markdown.
    Return only the markdown with no explanation text.
    Do not exclude any content from the page.
    """

    BOUNDING_BOX_PROMPT = """
    Convert the following PDF page to markdown.
    Return only the markdown with no explanation text.
    Do not exclude any content from the page.
    Include the bounding box coordinates of any inline images.
    """
