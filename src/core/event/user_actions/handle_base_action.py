from typing import Dict, List, Any, Tuple
import anthropic
import logging
import traceback

SOLUTION_TAG_OPEN = "<solution>"
SOLUTION_TAG_CLOSE = "</solution>"


logger = logging.getLogger(__name__)


class BaseActionHandler:
    """Base class for handling user actions with tools and responses"""

    def __init__(
        self,
        client: anthropic.Anthropic,
        system_prompt_file: str,
        tools: List[Dict],
        tools_map: Dict,
        model: str,
    ):
        """
        Initialize the action handler

        Args:
            system_prompt_file: Path to system prompt file
            tools: List of available tools and their schemas
            tools_map: Mapping of tool names to their implementation functions
            model: Model to use for completions
        """
        self.client = client
        self.system_prompt_file = system_prompt_file
        self.tools = tools
        self.tools_map = tools_map
        self.model = model

    def handle_action(
        self, messages: List[Dict], max_tool_calls: int = 5
    ) -> Dict[str, Any]:
        """
        Handle a user action through chain-of-thought reasoning and tool usage

        Args:
            messages: Initial message stream
            max_tool_calls: Maximum number of tool calls allowed

        Returns:
            Dict containing final response and collected knowledge base responses
        """
        # Load system prompt
        with open(self.system_prompt_file, "r", encoding="utf8") as fp:
            sysprompt = fp.read()

        # Initialize response tracking
        kb_responses = []
        tool_calls_made = 0

        response = self.client.messages.create(
            model=self.model,
            system=sysprompt,
            max_tokens=4096,
            tools=self.tools,
            tool_choice={"type": "auto"},
            messages=messages,
        )

        while tool_calls_made < max_tool_calls:
            try:
                if not response.content:
                    break

                for content in response.content:
                    # Handle text thoughts
                    if hasattr(content, "text"):
                        self.append_message(messages, "assistant", content.text)
                        continue

                    # Handle tool calls
                    if hasattr(content, "name") and hasattr(content, "input"):
                        tool_name = content.name
                        tool_input = content.input

                        logger.info("Tool name: %s", tool_name)
                        logger.info("Tool input: %s", tool_input)

                        if not tool_name or tool_name not in self.tools_map:
                            self.append_message(
                                messages,
                                "assistant",
                                "Invalid tool requested. Let me reconsider my approach.",
                            )
                            continue

                        try:
                            kb_response, function_response = self.tools_map[tool_name](
                                **tool_input
                            )
                            self.handle_tool_response(
                                tool_name, function_response, messages
                            )
                            kb_responses.extend(kb_response)
                        except Exception as e:
                            logger.error("Tool execution error: %s", str(e))
                            self.append_message(
                                messages,
                                "assistant",
                                f"Encountered an error with {tool_name}. Let me try a different approach.",
                            )
                            function_response = str(e)
                            self.handle_tool_response(
                                tool_name, function_response, messages
                            )

                        tool_calls_made += 1

                if response.stop_reason != "tool_use":
                    break

                response = self.client.messages.create(
                    model=self.model,
                    system=sysprompt,
                    max_tokens=4096,
                    tools=self.tools,
                    tool_choice={"type": "auto"},
                    messages=messages,
                )   

            except Exception as e:
                logger.error("Error in main loop: %s", str(e))
                traceback.print_exc()
                self.append_message(
                    messages,
                    "assistant",
                    "Encountered an unexpected error. Let me try to formulate a response with the information I have.",
                )
                break

        final_response = self.generate_final_response(response)

        return {
            "response": final_response,
            "kb_responses": kb_responses,
        }

    def append_message(
        self, messages: List[Dict[str, str]], role: str, content: str
    ) -> None:
        """
        Appends a message to the message stream.

        Args:
            messages: List of message dictionaries
            role: Role of the message sender ('assistant' or 'user')
            content: The message content to append

        Returns:
            {"response": final_response, "kb_responses": kb_responses}

        """
        messages.append({"role": role, "content": content})

    def handle_tool_response(
        self, tool_name: str, function_response: str, messages: List[Dict[str, str]]
    ) -> Tuple[str, int]:
        """
        Handles the tool response and updates messages and KB responses accordingly.

            Args:
                tool_name: Name of the tool that was called
                function_response: Response from the tool
            messages: List of message dictionaries to update
        """
        self.append_message(
            messages, "user", f"Results from {tool_name}: {function_response}"
        )

    def generate_final_response(
        self,
        last_message: Dict[str, Any],
    ) -> str:
        """Generate the final response after tool usage

        Args:
            last_message (Dict[str, Any]): The last message from the agent

        Returns:
            str: The final response
        """
        final_response = None

        if last_message.content:
            for content in last_message.content:
                if hasattr(content, "text"):
                    if (
                        SOLUTION_TAG_OPEN in content.text
                        and SOLUTION_TAG_CLOSE in content.text
                    ):
                        final_response = (
                            content.text.split(SOLUTION_TAG_OPEN)[1]
                            .split(SOLUTION_TAG_CLOSE)[0]
                            .strip()
                        )
                        break

        return final_response
