import re

# Package imports
from ..constants.patterns import Patterns


def format_markdown(text: str, bounding_boxes: list = None) -> str:
    """Format markdown text by removing markdown and code blocks and adding bounding box coordinates"""

    formatted_markdown = re.sub(Patterns.MATCH_MARKDOWN_BLOCKS, r"\1", text)
    formatted_markdown = re.sub(Patterns.MATCH_CODE_BLOCKS, r"\1", formatted_markdown)

    if bounding_boxes:
        bounding_box_markdown = "\n\n".join(
            [
                f"![Image](data:image/png;base64,{box['image']})\n\nBounding Box: {box['bounding_box']}"
                for box in bounding_boxes
            ]
        )
        formatted_markdown += f"\n\n{bounding_box_markdown}"

    return formatted_markdown
