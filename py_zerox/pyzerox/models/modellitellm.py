import os
import aiohttp
import warnings
import litellm
from typing import List, Dict, Any, Optional

# Package Imports
from .base import BaseModel
from .types import CompletionResponse
from ..errors import ModelAccessError, NotAVisionModel, MissingEnvironmentVariables
from ..constants.messages import Messages
from ..constants.prompts import Prompts
from ..processor.image import encode_image_to_base64

DEFAULT_SYSTEM_PROMPT = Prompts.DEFAULT_SYSTEM_PROMPT


class litellmmodel(BaseModel):
    ## setting the default system prompt
    _system_prompt = DEFAULT_SYSTEM_PROMPT

    def __init__(
        self,
        model: Optional[str] = None,
        **kwargs,
    ):
        """
        Initializes the Litellm model interface.
        :param model: The model to use for generating completions, defaults to "gpt-4o-mini". Refer: https://docs.litellm.ai/docs/providers
        :type model: str, optional
        
        :param kwargs: Additional keyword arguments to pass to self.completion -> litellm.completion. Refer: https://docs.litellm.ai/docs/providers and https://docs.litellm.ai/docs/completion/input
        """
        super().__init__(model=model, **kwargs)

        ## calling custom methods to validate the environment and model
        self.validate_environment()
        self.validate_model()
        self.validate_access()

    @property
    def system_prompt(self) -> str:
        '''Returns the system prompt for the model.'''
        return self._system_prompt
    
    @system_prompt.setter
    def system_prompt(self, prompt: str) -> None:
        '''
        Sets/overrides the system prompt for the model.
        Will raise a friendly warning to notify the user. 
        '''
        warnings.warn(f"{Messages.CUSTOM_SYSTEM_PROMPT_WARNING}. Default prompt for zerox is:\n {DEFAULT_SYSTEM_PROMPT}")
        self._system_prompt = prompt

    ## custom method on top of BaseModel
    def validate_environment(self) -> None:
        """Validates the environment variables required for the model."""
        env_config = litellm.validate_environment(model=self.model)

        if not env_config["keys_in_environment"]:
            raise MissingEnvironmentVariables(extra_info=env_config)
        
    def validate_model(self) -> None:
        '''Validates the model to ensure it is a vision model.'''
        if not litellm.supports_vision(model=self.model):
            raise NotAVisionModel(extra_info={"model": self.model})
        
    def validate_access(self) -> None:
        """Validates access to the model -> if environment variables are set correctly with correct values."""
        if not litellm.check_valid_key(model=self.model,api_key=None):
            raise ModelAccessError(extra_info={"model": self.model})
        

    async def completion(
        self,
        image_path: str,
        maintain_format: bool,
        prior_page: str,
    ) -> CompletionResponse:
        """LitellM completion for image to markdown conversion.

        :param image_path: Path to the image file.
        :type image_path: str
        :param maintain_format: Whether to maintain the format from the previous page.
        :type maintain_format: bool
        :param prior_page: The markdown content of the previous page.
        :type prior_page: str

        :return: The markdown content generated by the model.
        """
        messages = await self._prepare_messages(
            image_path=image_path,
            maintain_format=maintain_format,
            prior_page=prior_page,
        )

        try:
            response = await litellm.acompletion(model=self.model, messages=messages, **self.kwargs)

            ## completion response
            response = CompletionResponse(
                    content=response["choices"][0]["message"]["content"],
                    input_tokens=response["usage"]["prompt_tokens"],
                    output_tokens=response["usage"]["completion_tokens"],
                    bounding_boxes=response["choices"][0]["message"].get("bounding_boxes", []),
                )
            return response
        
        except Exception as err:
            raise Exception(Messages.COMPLETION_ERROR.format(err))

    async def _prepare_messages(
        self,
        image_path: str,
        maintain_format: bool,
        prior_page: str,
    ) -> List[Dict[str, Any]]:
        """Prepares the messages to send to the LiteLLM Completion API.

        :param image_path: Path to the image file.
        :type image_path: str
        :param maintain_format: Whether to maintain the format from the previous page.
        :type maintain_format: bool
        :param prior_page: The markdown content of the previous page.
        :type prior_page: str
        """
        # Default system message
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": self._system_prompt,
            },
        ]

        # If content has already been generated, add it to context.
        # This helps maintain the same format across pages.
        if maintain_format and prior_page:
            messages.append(
                {
                    "role": "system",
                    "content": f'Markdown must maintain consistent formatting with the following page: \n\n """{prior_page}"""',
                },
            )

        # Add Image to request
        base64_image = await encode_image_to_base64(image_path)
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        )

        return messages
