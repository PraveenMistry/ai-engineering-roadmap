"""
Day 11 — Exercise 2: MCP Client

The important concept here: capability discovery. This client does NOT
hardcode "call the search_policy Python function" — it asks the server
what tools exist, confirms search_policy is among them, THEN calls it
by name. If the server later added a second tool, this client would see
it without any code change here.
"""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = "mcp_server.py"


async def run_client(query: str):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_SCRIPT],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1: Discover — don't assume what's on the server
            tools_response = await session.list_tools()
            tool_names = [t.name for t in tools_response.tools]
            print(f"Discovered tools: {tool_names}")

            if "search_policy" not in tool_names:
                print("search_policy tool not found on this server.")
                return

            # Step 2: Invoke the discovered tool by name
            print(f"\nCalling search_policy(query='{query}')...")
            result = await session.call_tool("search_policy", arguments={"query": query})

            # Step 3: Print the result
            for content_block in result.content:
                if content_block.type == "text":
                    try:
                        parsed = json.loads(content_block.text)
                        print("\nResult:")
                        print(json.dumps(parsed, indent=2))
                    except json.JSONDecodeError:
                        print(content_block.text)


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "remote work"
    asyncio.run(run_client(query))
