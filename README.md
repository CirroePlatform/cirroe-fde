# cirroe-fde

This repository contains the source code for a project that interacts with users through a system like Discord and utilizes AI to process and respond to their messages.

Directory Structure:

./
├── include
│   └── utils.py
├── src
│   ├── core
│   │   ├── event
│   │   │   ├── user_actions
│   │   │   │   ├── handle_base_action.py
│   │   │   │   ├── handle_discord_message.py
│   │   │   │   └── handle_issue.py
│   │   ├── tools.py
│   │   └── __init__.py
│   ├── integrations
│   │   ├── cleaners
│   │   │   ├── base_cleaner.py
│   │   │   ├── html_cleaner.py
│   │   │   └── traceback_cleaner.py
│   │   └── kbs
│   │       ├── base_kb.py
│   │       ├── cloud_kb.py
│   │       ├── documentation_kb.py
│   │       ├── github_kb.py
│   │       └── issue_kb.py
│   ├── model
│   │   ├── auth.py
│   │   ├── code.py
│   │   ├── documentation.py
│   │   └── issue.py
│   ├── storage
│   │   └── vector.py
│   └── __init__.py
└── main.py
Files:

/include/utils.py
This file contains utility functions used throughout the project. It includes functions for:

Extracting the number of tokens from a string

Extracting image links from a content string

/src/core/event/user_actions/handle_base_action.py

This file defines the base class for handling user actions. It provides functionality for:

Initializing the action handler

Processing a user message through chain-of-thought reasoning and tool usage

Appending messages to the message stream

Handling tool responses

/src/core/event/user_actions/handle_discord_message.py

This file implements a class for handling Discord messages. It inherits from the BaseActionHandler and specializes its behavior for processing Discord messages.

/src/core/event/user_actions/handle_issue.py
This file implements a class for handling issues. It inherits from the BaseActionHandler and specializes its behavior for processing issues. It includes logic for:

Constructing the initial message stream from an issue

Processing an issue and generating a response using the AI agent

/src/integrations/kbs/.

These files define various knowledge base integrations used by the project.

/src/model/.
These files define models used by the project, potentially including models for representing issues, users, and responses.

/src/storage/.
These files define functionalities for storing and retrieving data.

/main.py
This file serves as the entry point for the application.

Dependencies

This project likely depends on several external libraries, such as:

anthropic - Python library for interacting with the Anthropic API
dotenv - Python library for loading environment variables from a .env file
httpx - Python asynchronous HTTP client for fetching images
Getting Started

Clone this repository.
Install required dependencies using pip install -r requirements.txt (assuming a requirements.txt file exists).
Configure environment variables (e.g., API keys) using a .env file.
Run the application using python main.py.
Note:

This is a general overview based on the provided code snippets. Specific details about configuration, environment variables, and usage might vary depending on the project's implementation.
