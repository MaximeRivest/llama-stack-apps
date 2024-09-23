# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed in accordance with the terms of the Llama 3 Community License Agreement.

import asyncio

import fire

# from common.client_utils import make_agent_config_with_custom_tools

# from multi_turn import (
#     execute_turns,
#     # load_api_keys_from_env,
#     # make_agent_config_with_custom_tools,
#     # prompt_to_turn,
#     # QuickToolConfig,
#     # search_tool_defn,
# )
from llama_stack import LlamaStack

from llama_stack.types import SamplingParams, UserMessage
from llama_stack.types.agent_create_params import AgentConfig
from sdk_common.agents.event_logger import EventLogger

from sdk_common.client_utils import load_api_keys_from_env, search_tool_defn
from termcolor import cprint


async def run_main(host: str, port: int, disable_safety: bool = False):
    client = LlamaStack(
        base_url=f"http://{host}:{port}",
    )

    custom_tools = []

    tool_definitions = [search_tool_defn(load_api_keys_from_env())]
    input_shields = []
    output_shields = []

    if not disable_safety:
        for t in tool_definitions:
            t["input_shields"] = ["llama_guard"]
            t["output_shields"] = ["llama_guard", "injection_shield"]

        input_shields = ["llama_guard", "jailbreak_shield"]
        output_shields = ["llama_guard"]

    agent_config = AgentConfig(
        model="Meta-Llama3.1-8B-Instruct",
        instructions="You are a helpful assistant",
        sampling_params=SamplingParams(strategy="greedy", temperature=1.0, top_p=0.9),
        tools=tool_definitions,
        tool_choices="auto",
        tool_prompt_format="function_tag",
        input_shields=input_shields,
        output_shields=output_shields,
        enable_session_persistence=False,
    )

    agentic_system_create_response = client.agents.create(
        agent_config=agent_config,
    )
    print(agentic_system_create_response)

    agentic_system_create_session_response = client.agents.sessions.create(
        agent_id=agentic_system_create_response.agent_id,
        session_name="test_session",
    )
    print(agentic_system_create_session_response)

    user_prompts = [
        "Hello",
        "Which players played in the winning team of the NBA western conference semifinals of 2024, please use tools",
    ]

    for content in user_prompts:
        cprint(f"User> {content}", color="white", attrs=["bold"])

        response = client.agents.turns.create(
            agent_id=agentic_system_create_response.agent_id,
            session_id=agentic_system_create_session_response.session_id,
            messages=[
                UserMessage(content=content, role="user"),
            ],
            stream=True,
        )

        async for log in EventLogger().log(response):
            log.print()

    # agent_config = asyncio.run(
    #     make_agent_config_with_custom_tools(
    #         tool_config=QuickToolConfig(
    #             builtin_tools=[
    #                 search_tool_defn(load_api_keys_from_env()),
    #             ],
    #         ),
    #         disable_safety=disable_safety,
    #     )
    # )
    # asyncio.run(
    #     execute_turns(
    #         agent_config=agent_config,
    #         custom_tools=[],
    #         turn_inputs=[
    #             prompt_to_turn("Hello"),
    #             prompt_to_turn(
    #                 "Which players played in the winning team of the NBA western conference semifinals of 2024, please use tools"
    #             ),
    #         ],
    #         host=host,
    #         port=port,
    #     )
    # )


def main(host: str, port: int, disable_safety: bool = False):
    asyncio.run(run_main(host, port, disable_safety))


if __name__ == "__main__":
    fire.Fire(main)
